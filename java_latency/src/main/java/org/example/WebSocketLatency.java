package org.example;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import java.net.URI;
import java.nio.ByteBuffer;
import java.time.Instant;
import java.util.concurrent.*;
import java.time.Duration;

/**
 * 一个连接监听多个topic
 */
public class WebSocketLatency {
    private static final ObjectMapper objectMapper = new ObjectMapper();

    public static void main(String[] args) {
        String endpoint = "";
        try {
            TokenService ts = new TokenService();
            endpoint = ts.getToken();
        } catch (Exception e) {
            e.printStackTrace();
        }
        String finalEndpoint = endpoint;
        new Thread(() -> pingWebSocket(finalEndpoint)).start();
        new Thread(() -> connectWebSocket(finalEndpoint, "/contractMarket/tickerV2:XBTUSDTM", "tickerV2", WebSocketLatency::extractTS)).start();
        new Thread(() -> connectWebSocket(finalEndpoint, "/contractMarket/level2:XBTUSDTM", "level2", WebSocketLatency::extractTimestamp)).start();
        new Thread(() -> connectWebSocket(finalEndpoint, "/contractMarket/execution:XBTUSDTM", "execution", WebSocketLatency::extractTS)).start();
        new Thread(() -> connectWebSocket(finalEndpoint, "/contractMarket/level2Depth5:XBTUSDTM", "level2Depth5", WebSocketLatency::extractTSMill)).start();
    }

    public static void pingWebSocket(String endpoint) {
        try {
            WebSocketClient client = new WebSocketClient(new URI(endpoint)) {
                @Override
                public void onOpen(ServerHandshake handshakedata) {
                    System.out.println("WebSocket Opened");
                }

                @Override
                public void onMessage(String message) {
                    // Handle pong messages here if needed
                }

                @Override
                public void onMessage(ByteBuffer bytes) {}

                @Override
                public void onClose(int code, String reason, boolean remote) {
                    System.out.println("WebSocket Closed");
                }

                @Override
                public void onError(Exception ex) {
                    System.out.println("WebSocket Error: " + ex.getMessage());
                }
            };

            client.connectBlocking();

            ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
            scheduler.scheduleAtFixedRate(() -> {
                try {
                    Instant startTime = Instant.now();
                    client.send("{\"type\":\"ping\"}");
                    System.out.println("Ping sent at: " + startTime);
                } catch (Exception e) {
                    System.out.println("Ping error: " + e.getMessage());
                }
            }, 0, 500, TimeUnit.MILLISECONDS);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void connectWebSocket(String endpoint, String topic, String streamType, ExtractTimestampFunction extractTimestamp) {
        try {
            WebSocketClient client = new WebSocketClient(new URI(endpoint)) {
                @Override
                public void onOpen(ServerHandshake handshakedata) {
                    System.out.println("WebSocket Opened: " + streamType);
                    subscribe(this, topic);
                }

                @Override
                public void onMessage(String message) {
                    try {
                        Instant messageTimestamp = extractTimestamp.extractTimestamp(message);
                        Instant receiveTime = Instant.now();
                        Duration latency = Duration.between(messageTimestamp, receiveTime);
                        System.out.println(streamType + " - Received message latency: " + latency.toMillis() + " ms");
                    } catch (Exception e) {
                        System.out.println("Timestamp extraction error: " + e.getMessage());
                    }
                }

                @Override
                public void onMessage(ByteBuffer bytes) {}

                @Override
                public void onClose(int code, String reason, boolean remote) {
                    System.out.println("WebSocket Closed: " + streamType);
                }

                @Override
                public void onError(Exception ex) {
                    System.out.println("WebSocket Error: " + ex.getMessage());
                }
            };

            client.connectBlocking();

            ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
            scheduler.scheduleAtFixedRate(() -> {
                try {
                    client.sendPing();
                } catch (Exception e) {
                    System.out.println("Ping error: " + e.getMessage());
                }
            }, 0, 1000, TimeUnit.MILLISECONDS);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void subscribe(WebSocketClient client, String topic) {
        String msg = String.format("{\"type\":\"subscribe\", \"topic\":\"%s\"}", topic);
        client.send(msg);
        System.out.println("Subscribed to topic: " + topic);
    }

    public static Instant extractTS(String message) throws Exception {
        JsonNode jsonNode = objectMapper.readTree(message);
        long timestampNano = jsonNode.path("data").path("ts").asLong();
        if (timestampNano == 0) {
            throw new IllegalArgumentException("Invalid ts timestamp");
        }
        return Instant.ofEpochSecond(0, timestampNano);
    }

    public static Instant extractTSMill(String message) throws Exception {
        JsonNode jsonNode = objectMapper.readTree(message);
        long timestampNano = jsonNode.path("data").path("ts").asLong();
        if (timestampNano == 0) {
            throw new IllegalArgumentException("Invalid ts timestamp");
        }
        return Instant.ofEpochMilli(timestampNano / 1_000_000);
    }

    public static Instant extractTimestamp(String message) throws Exception {
        JsonNode jsonNode = objectMapper.readTree(message);
        long timestamp = jsonNode.path("data").path("timestamp").asLong();
        if (timestamp == 0) {
            throw new IllegalArgumentException("Invalid timestamp");
        }
        return Instant.ofEpochMilli(timestamp);
    }

    @FunctionalInterface
    interface ExtractTimestampFunction {
        Instant extractTimestamp(String message) throws Exception;
    }
}
