package com.kucoin.websocket;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.kucoin.constant.OnsiteInspectionConstants;
import com.kucoin.example.MyWebSocketClient;
import org.example.TokenService;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.drafts.Draft;
import org.java_websocket.handshake.ServerHandshake;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import javax.websocket.*;
import javax.websocket.server.ServerEndpoint;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.util.Base64;
import java.util.Map;

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
            URI uri = new URI("ws://localhost:8080/websocket");
            Session session = container.connectToServer(MyWebSocketClientEndpoint.class, uri);

            // 发送消息
            session.getBasicRemote().sendText("Hello, Server!");

            // 关闭连接
            session.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

}
