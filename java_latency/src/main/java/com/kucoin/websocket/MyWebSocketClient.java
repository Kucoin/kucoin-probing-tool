package com.kucoin.websocket;


import javax.websocket.*;

/**
 * @Author yomi
 * @created at 2024/11/11/11:04
 * @Version 1.0.0
 * @Description
 */
@ClientEndpoint
public class MyWebSocketClient {

    @OnOpen
    public void onOpen(Session session) {
        System.out.println("Connected to server: " + session.getId());
    }

    @OnMessage
    public void onMessage(String message) {
        System.out.println("Received message: " + message);
    }

    @OnClose
    public void onClose(Session session, CloseReason closeReason) {
        System.out.println("Connection closed: " + session.getId() + ", Reason: " + closeReason.getReasonPhrase());
    }
}
