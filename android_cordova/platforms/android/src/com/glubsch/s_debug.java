package com.glubsch;

import android.content.Context;
import android.os.Environment;
import android.util.Log;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * Created by windkol on 18.05.2015.
 */
public class s_debug {
    private Context mContext;

    public s_debug(Context ServiceContext) {
        mContext=ServiceContext;
    }

    public void write_to_file(String started) {
        SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss");
        started=sdf.format(new Date())+" "+started+"\n";

        String baseFolder="";
        // check if external storage is available
        if(Environment.getExternalStorageState().equals(Environment.MEDIA_MOUNTED)) {
            baseFolder = mContext.getExternalFilesDir(null).getAbsolutePath();
        }
        // revert to using internal storage
        else {
            baseFolder = mContext.getFilesDir().getAbsolutePath();
        }
        // 2015 12 04 redirect file to download to be able to access it
        baseFolder = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS).getAbsolutePath()+"/";

        // delete old files
        String old_date = new SimpleDateFormat("yyyy_MM_dd").format(new Date(System.currentTimeMillis()-5*24*60*60*1000));
        File file = new File(baseFolder + "bg_service_"+old_date+".txt");
        if(file.exists()){
            file.delete();
        }

        // create/append new file
        String date = new SimpleDateFormat("yyyy_MM_dd").format(new Date());
        file = new File(baseFolder + "bg_service_"+date+".txt");
        FileOutputStream fos = null;
        try {
            fos = new FileOutputStream(file,true);
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        }
        try {
            fos.write(started.getBytes());
        } catch (IOException e) {
            e.printStackTrace();
        }
        try {
            fos.close();
        } catch (IOException e) {
            e.printStackTrace();
        }

        // debug output
        Log.i(mContext.getString(R.string.debug_id), baseFolder);
        Log.i(mContext.getString(R.string.debug_id), started);
    }
}
