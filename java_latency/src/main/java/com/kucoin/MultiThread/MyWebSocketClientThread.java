package com.kucoin.MultiThread;


import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.example.TokenService;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;

import java.net.URI;
import java.time.Duration;
import java.time.Instant;

/**
 * @Author yomi
 * @created at 2024/11/06/14:12
 * @Version 1.0.0
 * @Description ws多线程
 */
public class MyWebSocketClientThread extends WebSocketClient {

    private static final ObjectMapper objectMapper = new ObjectMapper();

    public MyWebSocketClientThread(URI serverUri) {
        super(serverUri);
    }

    @Override
    public void onOpen(ServerHandshake handshakedata) {
        // 当连接打开时，发送订阅消息
//        new Thread(() -> subscribeToTopics("{\"type\":\"subscribe\", \"topic\":\"/contractMarket/tickerV2:XBTUSDTM\"}")).start();
//        new Thread(() -> subscribeToTopics("{\"type\":\"subscribe\", \"topic\":\"/contractMarket/execution:XBTUSDTM\"}")).start();
        subscribeToTopics("");
    }

    @Override
    public void onMessage(String message) {
        // 处理接收到的消息
        dealTime(message);

    }

    @Override
    public void onClose(int code, String reason, boolean remote) {
        // 当连接关闭时，可以做一些清理工作
        System.out.println("Connection closed.");
    }

    @Override
    public void onError(Exception ex) {
        // 处理错误情况
        ex.printStackTrace();
    }

    private void subscribeToTopics(String msg) {
        // 订阅多个主题
        String msg1 = String.format("{\"type\":\"subscribe\", \"topic\":\"%s\"}", "/contractMarket/tickerV2:XBTUSDTM");
        String msg2 = String.format("{\"type\":\"subscribe\", \"topic\":\"%s\"}", "/contractMarket/execution:XBTUSDTM");
//        try {
//            Thread.sleep(1000);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }
        send(msg1);
        send(msg2);

    }


    public Duration dealTime(String message) {
        Instant messageTimestamp = null;
        try {
            messageTimestamp = extractTS(message);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
        Instant receiveTime = Instant.now();
        Duration latency = Duration.between(messageTimestamp, receiveTime);
        System.out.println(" - Received message latency: " + latency.toMillis() + " ms");
        return latency;
    }

    public static Instant extractTS(String message) throws Exception {
        JsonNode jsonNode = objectMapper.readTree(message);
        long timestampNano = jsonNode.path("data").path("ts").asLong();
        if (timestampNano == 0) {
            throw new IllegalArgumentException("Invalid ts timestamp, message : " + message);
        }
        return Instant.ofEpochSecond(0, timestampNano);
    }

    public static void main(String[] args) {
        try {
            TokenService ts = new TokenService();
            String endpoint = ts.getToken();
            System.out.println("endpoint----" + endpoint);
            URI uri = new URI(endpoint);
            MyWebSocketClientThread client = new MyWebSocketClientThread(uri);
            client.connect();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
