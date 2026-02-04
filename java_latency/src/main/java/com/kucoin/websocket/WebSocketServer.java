package com.kucoin.websocket;

import javax.websocket.OnClose;
import javax.websocket.OnMessage;
import javax.websocket.OnOpen;
import javax.websocket.Session;
import javax.websocket.server.ServerEndpoint;
import java.io.IOException;

/**
 * @Author yomi
 * @created at 2024/11/07/10:03
 * @Version 1.0.0
 * @Description
 */
@ServerEndpoint("/websocket")
public class WebSocketServer {

    @OnOpen
    public void onOpen(Session session) {
        System.out.println("【连接成功】Connected: " + session + " ----id: " + session.getId());

    }

    @OnMessage
    public void onMessage(String message, Session session) throws IOException {
        System.out.println("Received: " + message);
        session.getBasicRemote().sendText("【收到消息处理后发回去】Echo: " + message);

    }

    @OnClose
    public void onClose(Session session) {
        System.out.println("【断开链接】Disconnected: " + session + " ----id: " + session.getId());

    }

}
