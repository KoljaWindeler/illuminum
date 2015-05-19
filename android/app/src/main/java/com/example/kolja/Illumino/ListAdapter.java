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

    ArrayList<ImageView> webcam_pics=new ArrayList<ImageView>();
    ArrayList<TextView> updated = new ArrayList<TextView>();
    ArrayList<TextView> state = new ArrayList<TextView>();





    public ListAdapter (Context context, int layoutResourceId, ListContainer[] data) {
        super(context, layoutResourceId, data);
        this.layoutResourceId = layoutResourceId;
        this.context = context;
        this.data = data;
    }

    @Override
    public View getView(final int position, View convertView, ViewGroup parent) {
        View row = convertView;
        ListInfoHolder holder = new ListInfoHolder();

        LayoutInflater inflater = ((Activity)context).getLayoutInflater();
        row = inflater.inflate(layoutResourceId, parent, false);

        // button
        holder.webcam_on_off = (ImageButton) row.findViewById(R.id.webcam_on_off);
        holder.webcam_on_off.setTag(position);

        if(data[position].webcam_on){
            holder.webcam_on_off.setImageResource(R.drawable.red);
        } else {
            holder.webcam_on_off.setImageResource(R.drawable.green);
        }

        holder.webcam_on_off.setOnClickListener(new View.OnClickListener() {

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
        holder.webcam_pic=(ImageView)row.findViewById(R.id.webcam_pic);
        holder.webcam_pic.setTag(position);
        // save it to the queue
        if(webcam_pics.size()>position) {
            webcam_pics.set(position, holder.webcam_pic);
        } else {
            webcam_pics.add(position, holder.webcam_pic);
        }
        // this must be under the saving, otherwise everything go to hell ... why ever
        if(isPicOpen(position)){ // in this case this is more like a: should it be open
            showPic(position);
            if(data[position].last_img!=null) {
                holder.webcam_pic.setImageBitmap(data[position].last_img);
            }
        }

        //// text ////
        holder.Alias=(TextView)row.findViewById(R.id.Alias);
        holder.Alias.setTag(position);
        holder.Alias.setText(data[position].alias);

        holder.updated=(TextView)row.findViewById(R.id.LastUpdated);
        holder.updated.setTag(position);
        holder.updated.setText(String.valueOf(data[position].last_seen));
        if(updated.size()>position) {
            updated.set(position, holder.updated);
        } else {
            updated.add(position, holder.updated);
        }
        setUpdated(position);

        holder.state=(TextView)row.findViewById(R.id.State);
        holder.state.setTag(position);
        if(state.size()>position) {
            state.set(position, holder.state);
        } else {
            state.add(position, holder.state);
        }
        setState(position);


        row.setTag(holder);
        return row;
    }

    public void showPic(Integer pos) {
        setPicSize(pos, 1280, 720);
    }

    public void closePic(Integer pos) {
        setPicSize(pos, 0, 0);
    }

    private void setPicSize(Integer pos, int width, int height) {
        ImageView webcam_pic=webcam_pics.get(pos);
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
        TextView label=state.get(pos);
        String textversion="Status: ";
        if(data[pos].state==0){
            textversion+="Idle";
        } else if(data[pos].state==1){
            textversion+="Alarm";
        } else {
            textversion+="Error";
        }
        label.setText(textversion);
    }

    public void setUpdated(Integer pos){
        TextView label=updated.get(pos);
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
