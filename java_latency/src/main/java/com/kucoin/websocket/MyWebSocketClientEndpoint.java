package com.kucoin.websocket;


import javax.websocket.*;

/**
 * @Author yomi
 * @created at 2024/11/07/17:45
 * @Version 1.0.0
 * @Description
 */
@ClientEndpoint
public class MyWebSocketClientEndpoint {

    @OnOpen
    public void onOpen(Session session) {
        System.out.println("[客户端] Connected to server: " + session.getId());
    }

    @OnMessage
    public void onMessage(String message, Session session) {
        System.out.println("[客户端] Received message from server: " + message);
    }

    @OnClose
    public void onClose(Session session) {
        System.out.println("[客户端] Disconnected from server: " + session.getId());
    }
}
