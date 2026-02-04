package main

import (
	"encoding/json"
	"fmt"
	"go_latency/token"
	"log"
	"time"

	"github.com/gorilla/websocket"
)

type GenericData struct {
	Data struct {
		TimestampNano int64 `json:"ts"`
		Timestamp     int64 `json:"timestamp"`
	} `json:"data"`
}

func pingWebSocket(endpoint string) {
	c, _, err := websocket.DefaultDialer.Dial(endpoint, nil)
	if err != nil {
		log.Fatal("dial:", err)
	}
	defer c.Close()

	_, _, err = c.ReadMessage()
	if err != nil {
		log.Println("read:", err)
		return
	}

	streamType := "ping"
	msg := map[string]interface{}{
		"type": "ping",
	}
	done := make(chan struct{})
	defer close(done)

	ticker := time.NewTicker(1 * time.Second) // Triggers every second
	defer ticker.Stop()

	pingTicker := time.NewTicker(500 * time.Millisecond) // Triggers twice every second
	defer pingTicker.Stop()

	timestamps := make(chan time.Time, 100)
	defer close(timestamps)
	go handleLatency(timestamps, done, ticker, streamType) // Start the routine to calculate latency

	for {
		select {
		case <-pingTicker.C:
			startTime := time.Now() // Get the current time before sending the ping

			if err := c.WriteJSON(msg); err != nil {
				log.Fatal("write:", err)
			}

			_, _, err := c.ReadMessage()
			if err != nil {
				log.Println("read:", err)
				return
			}
			timestamps <- startTime // Send the time of sending the ping
		}
	}
}

func connectWebSocket(endpoint, topic, streamType string, extractTimestamp func([]byte) (time.Time, error)) {
	c, _, err := websocket.DefaultDialer.Dial(endpoint, nil)
	if err != nil {
		log.Fatal("dial:", err)
	}
	defer c.Close()

	_, _, err = c.ReadMessage()
	if err != nil {
		log.Println("read:", err)
		return
	}

	done := make(chan struct{})
	defer close(done)
	ticker := time.NewTicker(1 * time.Second) // Triggers every second
	defer ticker.Stop()

	pingTicker := time.NewTicker(time.Duration(token.Result.Data.InstanceServers[0].PingInterval) * time.Millisecond)
	defer pingTicker.Stop()

	timestamps := make(chan time.Time, 100) // Channel to hold timestamps
	defer close(timestamps)
	messages := make(chan []byte, 100)
	defer close(messages)
	go handleLatency(timestamps, done, ticker, streamType) // Handle latency in separate goroutine

	subscribe(c, topic) // Subscribe to the topic

	go func() {
		for {
			_, message, err := c.ReadMessage()
			if err != nil {
				log.Println("read:", err)
				return
			}
			messages <- message
		}
	}()

	go func() {
		for msg := range messages {
			ts, err := extractTimestamp(msg)
			if err != nil {
				// log.Printf("Error extracting timestamp: %v", err)
				continue
			}
			timestamps <- ts
		}
	}()

	for {
		select {
		case <-pingTicker.C:
			if err := c.WriteMessage(websocket.PingMessage, nil); err != nil {
				log.Println("ping:", err)
				return
			}
		}
	}
}

func handleLatency(timestamps chan time.Time, done chan struct{}, ticker *time.Ticker, streamType string) {
	var totalLatency time.Duration
	var count int
	for {
		select {
		case <-done:
			return
		case t := <-timestamps:
			latency := time.Since(t)
			totalLatency += latency
			count++
		case <-ticker.C:
			if count > 0 {
				avgLatency := totalLatency / time.Duration(count)
				// single way of latency
				if streamType == "ping" {
					avgLatency = avgLatency / 2
				}
				log.Printf("%s: Average latency (per second): %v, count: %v", streamType, avgLatency, count)
				totalLatency = 0
				count = 0
			}
		}
	}
}

func subscribe(c *websocket.Conn, topic string) {
	msg := map[string]interface{}{
		"type":  "subscribe",
		"topic": topic,
	}
	if err := c.WriteJSON(msg); err != nil {
		log.Fatal("write:", err)
	}
}

// execution use mirco timestamp
func extractTSMill(message []byte) (time.Time, error) {
	var msg GenericData
	if err := json.Unmarshal(message, &msg); err != nil {
		return time.Time{}, err
	}
	if msg.Data.TimestampNano == 0 {
		return time.Time{}, fmt.Errorf("invalid ts timestamp")
	}
	return time.Unix(0, msg.Data.TimestampNano*int64(time.Millisecond)), nil
}

func extractTS(message []byte) (time.Time, error) {
	var msg GenericData
	if err := json.Unmarshal(message, &msg); err != nil {
		return time.Time{}, err
	}
	if msg.Data.TimestampNano == 0 {
		return time.Time{}, fmt.Errorf("invalid ts timestamp")
	}
	return time.Unix(0, msg.Data.TimestampNano), nil
}

func extractTimestamp(message []byte) (time.Time, error) {
	var msg GenericData
	if err := json.Unmarshal(message, &msg); err != nil {
		return time.Time{}, err
	}
	if msg.Data.Timestamp == 0 {
		return time.Time{}, fmt.Errorf("invalid timestamp")
	}
	return time.Unix(0, msg.Data.Timestamp*int64(time.Millisecond)), nil
}

func main() {
	endpoint, _, err := token.GetToken()
	if err != nil {
		log.Fatal("Error fetching token:", err)
	}
	go pingWebSocket(endpoint)
	go connectWebSocket(endpoint, "/contractMarket/tickerV2:XBTUSDTM", "tickerV2", extractTS)
	go connectWebSocket(endpoint, "/contractMarket/level2:XBTUSDTM", "level2", extractTimestamp)
	go connectWebSocket(endpoint, "/contractMarket/execution:XBTUSDTM", "execution", extractTS)
	go connectWebSocket(endpoint, "/contractMarket/level2Depth5:XBTUSDTM", "level2Depth5", extractTSMill)

	select {}
}
