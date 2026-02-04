package com.kucoin.MultiThread;

import com.kucoin.constant.OnsiteInspectionConstants;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.util.Base64;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/**
 * @Author yomi
 * @created at 2024/11/04/15:44
 * @Version 1.0.0
 * @Description
 */
public class OnSiteInspectionExample {

    /**

     成功：
     Response Code: 200
     {"code":"200000","data":{"orderId":"672db6e2ab0f0a000727ffb1","clientOid":"5c52e11203aa677f33e493fb3"}}

     失败：
     Response Code: 200
     {"msg":"Client oid is duplicated","code":"400100"}

     */
    public static void main(String[] args) throws Exception {
//        createOrders();
//        createOrdersFutures();
        createOrdersMargin();
    }

    private static void createOrdersMargin() throws Exception {
        Instant receiveTime1 = Instant.now();

        String endpoint = "/api/v3/hf/margin/order";
        long now = System.currentTimeMillis();
        String dataJson = "{\n" +
                "    \"type\": \"limit\",\n" +
                "    \"symbol\": \"BTC-USDT\",\n" +
                "    \"side\": \"buy\",\n" +
                "    \"price\": \"50000\",\n" +
                "    \"size\": \"0.00001\",\n" +
                "    \"clientOid\": \"5c52e11203aa677f33e493fb1\",\n" +
                "    \"remark\": \"order remarks\"\n" +
                "}";
        String strToSign = now + "POST" + endpoint + dataJson;
        String signature = generateSignature(strToSign, OnsiteInspectionConstants.API_SECRET);
        String passphrase = generateSignature(OnsiteInspectionConstants.API_PASSPHRASE, OnsiteInspectionConstants.API_SECRET);

        URL url = new URL(OnsiteInspectionConstants.MARGIN_URL + endpoint);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();

        conn.setRequestMethod("POST");
        conn.setRequestProperty("KC-API-SIGN", signature);
        conn.setRequestProperty("KC-API-TIMESTAMP", String.valueOf(now));
        conn.setRequestProperty("KC-API-KEY", OnsiteInspectionConstants.API_KEY);
        conn.setRequestProperty("KC-API-PASSPHRASE", passphrase);
        conn.setRequestProperty("KC-API-KEY-VERSION", "2");
        conn.setRequestProperty("Content-Type", "application/json");
        conn.setDoOutput(true);


        try (OutputStream os = conn.getOutputStream()) {
            byte[] input = dataJson.getBytes(StandardCharsets.UTF_8);
            os.write(input, 0, input.length);
        }

        System.out.println("KC-API-KEY: " + OnsiteInspectionConstants.API_KEY + ", KC-API-SIGN: " + signature + ", KC-API-TIMESTAMP: " + String.valueOf(now) + ", KC-API-PASSPHRASE:" + passphrase);

        int responseCode = conn.getResponseCode();
        System.out.println("Response Code: " + responseCode);

        BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
        String inputLine;
        StringBuilder response = new StringBuilder();

        while ((inputLine = in.readLine()) != null) {
            response.append(inputLine);
        }

        in.close();

        Instant receiveTime2 = Instant.now();
        Duration latency = Duration.between(receiveTime1, receiveTime2);
        System.out.println("latency = " +  latency.toMillis() + "ms");

        JSONObject jsonObject = new JSONObject(response.toString());
        String code = jsonObject.getString("code");

        System.out.println(response.toString() + ", code = " + code);

    }

    private static void createOrdersFutures() throws Exception {
        Instant receiveTime1 = Instant.now();

        String endpoint = "/api/v1/orders";
        long now = System.currentTimeMillis();
        String dataJson = "{\n" +
                "    \"clientOid\": \"5c52e11203aa677f33e493fb1\",\n" +
                "    \"side\": \"buy\",\n" +
                "    \"symbol\": \"XBTUSDTM\",\n" +
                "    \"leverage\": 3,\n" +
                "    \"type\": \"limit\",\n" +
                "    \"remark\": \"order remarks\",\n" +
                "    \"reduceOnly\": false,\n" +
                "    \"marginMode\": \"CROSS\",\n" +
                "    \"price\": \"0.1\",\n" +
                "    \"size\": 1,\n" +
                "    \"timeInForce\": \"GTC\"\n" +
                "}";
        String strToSign = now + "POST" + endpoint + dataJson;
        String signature = generateSignature(strToSign, OnsiteInspectionConstants.API_SECRET);
        String passphrase = generateSignature(OnsiteInspectionConstants.API_PASSPHRASE, OnsiteInspectionConstants.API_SECRET);

        URL url = new URL(OnsiteInspectionConstants.FUTURES_URL + endpoint);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();

        conn.setRequestMethod("POST");
        conn.setRequestProperty("KC-API-SIGN", signature);
        conn.setRequestProperty("KC-API-TIMESTAMP", String.valueOf(now));
        conn.setRequestProperty("KC-API-KEY", OnsiteInspectionConstants.API_KEY);
        conn.setRequestProperty("KC-API-PASSPHRASE", passphrase);
        conn.setRequestProperty("KC-API-KEY-VERSION", "2");
        conn.setRequestProperty("Content-Type", "application/json");
        conn.setDoOutput(true);


        try (OutputStream os = conn.getOutputStream()) {
            byte[] input = dataJson.getBytes(StandardCharsets.UTF_8);
            os.write(input, 0, input.length);
        }

        System.out.println("KC-API-KEY: " + OnsiteInspectionConstants.API_KEY + ", KC-API-SIGN: " + signature + ", KC-API-TIMESTAMP: " + String.valueOf(now) + ", KC-API-PASSPHRASE:" + passphrase);

        int responseCode = conn.getResponseCode();
        System.out.println("Response Code: " + responseCode);

        BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
        String inputLine;
        StringBuilder response = new StringBuilder();

        while ((inputLine = in.readLine()) != null) {
            response.append(inputLine);
        }

        in.close();

        Instant receiveTime2 = Instant.now();
        Duration latency = Duration.between(receiveTime1, receiveTime2);
        System.out.println("latency = " +  latency.toMillis() + "ms");

        JSONObject jsonObject = new JSONObject(response.toString());
        String code = jsonObject.getString("code");

        System.out.println(response.toString() + ", code = " + code);

    }

    private static void createOrders() throws Exception {
        Instant receiveTime1 = Instant.now();

        String endpoint = "/api/v1/hf/orders";
        long now = System.currentTimeMillis();
        String dataJson = "{\"type\": \"limit\"," +
                "    \"symbol\": \"BTC-USDT\"," +
                "    \"side\": \"buy\"," +
                "    \"price\": \"50000\"," +
                "    \"size\": \"0.00001\"," +
                "    \"clientOid\": \"5c52e11203aa677f33e493fb3\"," +
                "    \"remark\": \"order remarks\"}";
        String strToSign = now + "POST" + endpoint + dataJson;
        String signature = generateSignature(strToSign, OnsiteInspectionConstants.API_SECRET);
        String passphrase = generateSignature(OnsiteInspectionConstants.API_PASSPHRASE, OnsiteInspectionConstants.API_SECRET);

        URL url = new URL(OnsiteInspectionConstants.SPOT_URL + endpoint);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();

        conn.setRequestMethod("POST");
        conn.setRequestProperty("KC-API-SIGN", signature);
        conn.setRequestProperty("KC-API-TIMESTAMP", String.valueOf(now));
        conn.setRequestProperty("KC-API-KEY", OnsiteInspectionConstants.API_KEY);
        conn.setRequestProperty("KC-API-PASSPHRASE", passphrase);
        conn.setRequestProperty("KC-API-KEY-VERSION", "2");
        conn.setRequestProperty("Content-Type", "application/json");
        conn.setDoOutput(true);


        try (OutputStream os = conn.getOutputStream()) {
            byte[] input = dataJson.getBytes(StandardCharsets.UTF_8);
            os.write(input, 0, input.length);
        }

        System.out.println("KC-API-KEY: " + OnsiteInspectionConstants.API_KEY + ", KC-API-SIGN: " + signature + ", KC-API-TIMESTAMP: " + String.valueOf(now) + ", KC-API-PASSPHRASE:" + passphrase);

        int responseCode = conn.getResponseCode();
        System.out.println("Response Code: " + responseCode);

        BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
        String inputLine;
        StringBuilder response = new StringBuilder();

        while ((inputLine = in.readLine()) != null) {
            response.append(inputLine);
        }

        in.close();

        Instant receiveTime2 = Instant.now();
        Duration latency = Duration.between(receiveTime1, receiveTime2);
        System.out.println("latency = " +  latency.toMillis() + "ms");

        JSONObject jsonObject = new JSONObject(response.toString());
        String code = jsonObject.getString("code");

        System.out.println(response.toString() + ", code = " + code);

    }


    private static String generateSignature(String data, String key) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        SecretKeySpec secretKeySpec = new SecretKeySpec(key.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
        mac.init(secretKeySpec);
        byte[] rawHmac = mac.doFinal(data.getBytes(StandardCharsets.UTF_8));

        return Base64.getEncoder().encodeToString(rawHmac);
    }

}
