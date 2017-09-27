package com.kuretru.singlenet;

import android.content.Context;
import android.os.Handler;
import android.os.Message;

import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class HttpHelper {

    private Context _context;
    private Handler _handler;

    public HttpHelper(Context context, Handler handler){
        _context = context;
        _handler = handler;
    }

    //通用GET方法
    private String doGet(String url) {
        try {
            URL address = new URL(url);
            HttpURLConnection urlConnection = (HttpURLConnection) address.openConnection();
            urlConnection.setConnectTimeout(10 * 000);
            urlConnection.connect();
            InputStreamReader isr = new InputStreamReader(
                    urlConnection.getInputStream(), "UTF-8");
            BufferedReader reader = new BufferedReader(isr);
            StringBuffer resultData = new StringBuffer();
            String temp = "";
            while ((temp = reader.readLine()) != null) {
                resultData.append(temp);
            }
            isr.close();
            urlConnection.disconnect();
            return resultData.toString();
        } catch (Exception e){
            e.printStackTrace();
        }
        return null;
    }

    //通用POST方法
    private String doPost(String url, String content){
        try {
            URL address = new URL(url);
            HttpURLConnection urlConnection = (HttpURLConnection) address.openConnection();
            urlConnection.setDoOutput(true);
            urlConnection.setDoInput(true);
            urlConnection.setRequestMethod("POST");
            urlConnection.setUseCaches(false);
            urlConnection.setInstanceFollowRedirects(true);
            urlConnection.setRequestProperty("Content-type","application/x-www-form-urlencoded");
            //urlConnection.setConnectTimeout(10 * 000);
            urlConnection.connect();

            DataOutputStream dos = new DataOutputStream(urlConnection.getOutputStream());
            byte[] bytes = content.getBytes();
            dos.write(bytes);
            dos.flush();
            dos.close();

            InputStreamReader isr = new InputStreamReader(
                    urlConnection.getInputStream(), "UTF-8");
            BufferedReader reader = new BufferedReader(isr);
            StringBuffer resultData = new StringBuffer();
            String temp = "";
            while ((temp = reader.readLine()) != null) {
                resultData.append(temp);
            }
            isr.close();
            urlConnection.disconnect();
            return resultData.toString();
        } catch (Exception e){
            e.printStackTrace();
        }
        return  null;
    }

    //发送GET请求并正则提取密码
    private void getPassword(String url){
        String respone = doGet(url);
        Pattern pattern = Pattern.compile("[0-9]{6}");
        Matcher matcher = pattern.matcher(respone);
        if (matcher.find()) {
            String code = matcher.group(0);
            Message msg = _handler.obtainMessage(2, code);
            _handler.sendMessage(msg);
        }
    }

    //发送POST请求设置密码
    private void setPassword(String url, String password, String secret){
        StringBuffer buffer = new StringBuffer();
        buffer.append("password=").append(password).append("&")
                .append("secret").append(secret).append("&");
        String respone = doPost(url, buffer.toString());
    }

    public void getRouterPassword(final String url){
        Thread t = new Thread(){
            public void run() {
                getPassword(url);
            }
        };
        t.start();
    }
}
