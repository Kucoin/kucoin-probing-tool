package org.example;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

public class TokenService {
    private static final String API_URL = "https://api.kucoin.com/api/v1/bullet-public";

    public String getToken() throws Exception {
        URL url = new URL(API_URL);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
        conn.setDoOutput(true);

        if (conn.getResponseCode() != HttpURLConnection.HTTP_OK) {
            throw new RuntimeException("Failed : HTTP error code : " + conn.getResponseCode());
        }

        BufferedReader br = new BufferedReader(new InputStreamReader((conn.getInputStream())));
        StringBuilder response = new StringBuilder();
        String output;
        while ((output = br.readLine()) != null) {
            response.append(output);
        }

        conn.disconnect();

        JSONObject jsonObject = new JSONObject(response.toString());
        if (!"200000".equals(jsonObject.getString("code"))) {
            throw new RuntimeException("API error with code: " + jsonObject.getString("code"));
        }

        JSONObject data = jsonObject.getJSONObject("data");
        if (data.getJSONArray("instanceServers").length() == 0) {
            throw new RuntimeException("no servers returned by API");
        }

        JSONObject firstServer = data.getJSONArray("instanceServers").getJSONObject(0);
        String endpoint = firstServer.getString("endpoint");
        String token = data.getString("token");

        return endpoint + "?token=" + token;
    }
}