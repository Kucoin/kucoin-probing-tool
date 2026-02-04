package com.kucoin.websocket;

import org.glassfish.tyrus.server.Server;


/**
 * @Author yomi
 * @created at 2024/11/11/11:11
 * @Version 1.0.0
 * @Description
 */
public class WebSocketServerTest {

    public static void main(String[] args) {
        Server server = new Server("localhost", 8080, "/", WebSocketServer.class);

        try {
            server.start();
            System.out.println("WebSocket server started");
            System.in.read();
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            server.stop();
        }
    }
}
