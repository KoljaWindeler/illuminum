package com.example.kolja.Illumino;


import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.SeekBar;
import android.widget.TextView;

import org.json.JSONException;
import org.json.JSONObject;

import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;

public class ListAdapter extends ArrayAdapter<ListContainer> {
    Context context;
    int layoutResourceId;
    ListContainer data[]=null;


    public ListAdapter (Context context, int layoutResourceId, ListContainer[] data) {
        super(context, layoutResourceId, data);
        this.layoutResourceId = layoutResourceId;
        this.context = context;
        this.data = data;
    }

    @Override
    public View getView(final int position, View convertView, ViewGroup parent) {
        View row = convertView;
        //ListInfoHolder holder = new ListInfoHolder();

        LayoutInflater inflater = ((Activity)context).getLayoutInflater();
        row = inflater.inflate(layoutResourceId, parent, false);

        // button
        ImageButton webcam_on_off = (ImageButton) row.findViewById(R.id.webcam_on_off);
        webcam_on_off.setTag(position);

        if(data[position].webcam_on){
            webcam_on_off.setImageResource(R.drawable.red);
        } else {
            webcam_on_off.setImageResource(R.drawable.green);
        }

        webcam_on_off.setOnClickListener(new View.OnClickListener() {

            @Override
            public void onClick(View v) {
                int interval=0;
                if(isPicOpen((Integer) v.getTag())){
                    ((ImageButton) v).setImageResource(R.drawable.green);
                    closePic((Integer) v.getTag());
                    data[(Integer) v.getTag()].webcam_on=false;
                    // fire message to switch off
                    interval=0;
                } else {
                    ((ImageButton) v).setImageResource(R.drawable.red);
                    showPic((Integer) v.getTag());
                    data[(Integer) v.getTag()].webcam_on=true;
                    interval=1;
                }

                // fire message
                JSONObject object_send = new JSONObject();
                try {
                    object_send.put("cmd", "set_interval");
                    object_send.put("mid", data[(Integer) v.getTag()].mid);
                    object_send.put("interval", interval);

                    Intent send_intent = new Intent(bg_service.SENDER);
                    send_intent.putExtra(s_ws.TYPE, s_ws.APP2SERVER);
                    send_intent.putExtra(s_ws.PAYLOAD, object_send.toString());
                    ((MainActivity) context).sendBroadcast(send_intent);
                } catch (JSONException e) {
                    e.printStackTrace();
                }
            }
        });

        //// image /////
        ImageView webcam_pic=(ImageView)row.findViewById(R.id.webcam_pic);
        webcam_pic.setTag(position);
        // save it to the queue
        data[position].webcam_pic=webcam_pic;

        // this must be under the saving, otherwise everything go to hell ... why ever
        if(isPicOpen(position)){ // in this case this is more like a: should it be open
            showPic(position);
            if(data[position].last_img!=null) {
                webcam_pic.setImageBitmap(data[position].last_img);
            }
        }

        //// text ////
        TextView alias=(TextView)row.findViewById(R.id.Alias);
        alias.setTag(position);
        alias.setText(data[position].alias);

        TextView updated=(TextView)row.findViewById(R.id.LastUpdated);
        updated.setTag(position);
        updated.setText(String.valueOf(data[position].last_seen));
        data[position].updateLabel=updated;
        setUpdated(position);

        TextView stateLabel=(TextView)row.findViewById(R.id.State);
        stateLabel.setTag(position);
        data[position].stateLabel=stateLabel;
        setState(position);


        //row.setTag(holder);
        return row;
    }

    public void showPic(Integer pos) {
        setPicSize(pos, 1280, 720);
    }

    public void closePic(Integer pos) {
        setPicSize(pos, 0, 0);
    }

    private void setPicSize(Integer pos, int width, int height) {
        ImageView webcam_pic=data[pos].webcam_pic;
        ViewGroup.LayoutParams params = webcam_pic.getLayoutParams();
        if(params.width!=width || params.height!=height) {
            params.width = width;
            params.height = height;
            webcam_pic.setLayoutParams(params);
        };
    }

    public boolean isPicOpen(Integer pos) {
        return data[pos].webcam_on;
    }

    public void setState(Integer pos){
        TextView label=data[pos].stateLabel;
        String textversion="Status: ";
        if(data[pos].state==0){
            textversion+="No Movement";
        } else if(data[pos].state==1){
            textversion+="Movement";
        } else {
            textversion+="Error";
        }

        if(data[pos].detection==0){
            textversion+=", not protected";
        } else if(data[pos].detection==1){
            textversion+=", protected";
        } else if(data[pos].detection==2){
            textversion+=", premium protected";
        } else {
            textversion+="Error";
        }
        label.setText(textversion);
    }

    public void setUpdated(Integer pos){
        TextView label=data[pos].updateLabel;
        String textversion="Last Ping: ";
        DateFormat sdf = new SimpleDateFormat("H:m:s");
        Date netDate = (new Date(data[pos].last_seen*1000));
        textversion+= sdf.format(netDate);
        label.setText(textversion);
    }

    static class ListInfoHolder
    {
        ImageButton webcam_on_off;
        TextView Alias;
        TextView updated;
        TextView state;
        ImageView webcam_pic;
    }



}
