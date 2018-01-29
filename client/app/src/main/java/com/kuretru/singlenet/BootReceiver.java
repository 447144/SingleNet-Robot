package com.kuretru.singlenet;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        Log.d("Singnet-DEBUG", "收到开机广播");
        Intent i = new Intent(context, AlarmService.class);
        context.startService(i);
    }
}