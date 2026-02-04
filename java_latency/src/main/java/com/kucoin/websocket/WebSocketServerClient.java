package com.kucoin.websocket;

import javax.websocket.*;
import java.net.URI;

/**
 * @Author yomi
 * @created at 2024/11/07/10:03
 * @Version 1.0.0
 * @Description
 */
public class WebSocketServerClient {

    public static void main(String[] args) {
        try {
            WebSocketContainer container = ContainerProvider.getWebSocketContainer();
            String uri = "ws://localhost:8080/websocket";
            System.out.println("Connecting to " + uri);
            Session session = container.connectToServer(MyWebSocketClient.class, URI.create(uri));
            session.getBasicRemote().sendText("Hello, WebSocket!");
            Thread.sleep(5000); // Wait for a while to receive messages
            session.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

}
