package com.kucoin.websocket;

/**
 * @Author yomi
 * @created at 2024/11/07/11:14
 * @Version 1.0.0
 * @Description
 */
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.websocket.server.ServerContainer;
import javax.websocket.server.ServerEndpointConfig;

@WebServlet(name = "WebSocketServlet", urlPatterns = {"/websocket"}, loadOnStartup = 1)
public class WebSocketServlet extends HttpServlet {

    @Override
    public void init() throws ServletException {
        super.init();
        ServerContainer serverContainer = (ServerContainer) getServletContext().getAttribute("javax.websocket.server.ServerContainer");
        try {
            serverContainer.addEndpoint(ServerEndpointConfig.Builder.create(WebSocketServer.class, "/websocket").build());
        } catch (Exception e) {
            throw new ServletException(e);

        }

    }

}

