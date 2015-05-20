package com.example.kolja.Illumino;


import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.BitmapFactory;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseExpandableListAdapter;
import android.widget.CheckedTextView;
import android.widget.ExpandableListView;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.TextView;
import android.util.SparseArray;
import android.widget.Toast;

import org.json.JSONException;
import org.json.JSONObject;

import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Date;

public class ListAdapter extends BaseExpandableListAdapter {
    Context context;
    private final SparseArray<areas> data;
    private final SparseArray<areas> groups;
    public LayoutInflater inflater;
    public Activity activity;


    public ListAdapter (Activity act, SparseArray<areas> groups) {
        this.context = act;
        this.data = groups;
        this.groups = groups;
        this.inflater = act.getLayoutInflater();
        this.activity = act;
    }

    @Override
    public Object getChild(int groupPosition, int childPosition) {
        return groups.get(groupPosition).m2mList.get(childPosition);
    }

    @Override
    public long getChildId(int groupPosition, int childPosition) {
        return 0;
    }

    @Override
    public View getChildView(int groupPosition, final int childPosition,boolean isLastChild, View convertView, ViewGroup parent) {
        TextView text = null;
        if (convertView == null) {
            convertView = inflater.inflate(R.layout.listentry, null);
        }
        // button
        ImageButton webcam_on_off = (ImageButton) convertView.findViewById(R.id.webcam_on_off);
        webcam_on_off.setTag(String.valueOf(groupPosition)+","+String.valueOf(childPosition));

        webcam_on_off.setOnClickListener(new View.OnClickListener() {

            @Override
            public void onClick(View v) {
                int interval=0;
                String Tag=(String) v.getTag();
                String[] TagArray=Tag.split(",");
                int gid=Integer.parseInt(TagArray[0]);
                int cid=Integer.parseInt(TagArray[1]);


                if(isPicOpen(gid,cid)){
                    ((ImageButton) v).setImageResource(R.drawable.green);
                    closePic(gid,cid);
                    data.get(gid).m2mList.get(cid).webcam_on=false;
                    // fire message to switch off
                    interval=0;
                } else {
                    ((ImageButton) v).setImageResource(R.drawable.red);
                    showPic(gid,cid);
                    if(data.get(gid).m2mList.get(cid).last_img!=null) {
                        data.get(gid).m2mList.get(cid).webcam_pic.setImageBitmap(data.get(gid).m2mList.get(cid).last_img);
                    } else {
                        data.get(gid).m2mList.get(cid).webcam_pic.setImageBitmap(BitmapFactory.decodeResource(v.getContext().getResources(), R.drawable.webcam));
                    }
                    data.get(gid).m2mList.get(cid).webcam_on=true;
                    interval=1;
                }

                // fire message
                JSONObject object_send = new JSONObject();
                try {
                    object_send.put("cmd", "set_interval");
                    object_send.put("mid", data.get(gid).m2mList.get(cid).mid);
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
        ImageView webcam_pic=(ImageView)convertView.findViewById(R.id.webcam_pic);
        webcam_pic.setTag(String.valueOf(groupPosition)+","+String.valueOf(childPosition));
        // save it to the queue
        data.get(groupPosition).m2mList.get(childPosition).webcam_pic=webcam_pic;

        // this must be under the saving, otherwise everything go to hell ... why ever
        if(isPicOpen(groupPosition,childPosition)){ // in this case this is more like a: should it be open
            Log.i("Websocket22", "Picture "+String.valueOf(groupPosition) + "/" + String.valueOf(childPosition)+" shall be shown!");
            webcam_on_off.setImageResource(R.drawable.red);
            showPic(groupPosition,childPosition);
            if(data.get(groupPosition).m2mList.get(childPosition).last_img!=null) {
                webcam_pic.setImageBitmap(data.get(groupPosition).m2mList.get(childPosition).last_img);
            }
        } else {
            Log.i("Websocket22", "Picture "+String.valueOf(groupPosition) + "/" + String.valueOf(childPosition)+" shall NOT be shown!");
            webcam_on_off.setImageResource(R.drawable.green);
            closePic(groupPosition,childPosition);
        }

        //// text ////
        TextView alias=(TextView)convertView.findViewById(R.id.Alias);
        alias.setTag(String.valueOf(groupPosition)+","+String.valueOf(childPosition));
        alias.setText(data.get(groupPosition).m2mList.get(childPosition).alias);

        TextView updated=(TextView)convertView.findViewById(R.id.LastUpdated);
        updated.setTag(String.valueOf(groupPosition)+","+String.valueOf(childPosition));
        updated.setText(String.valueOf(data.get(groupPosition).m2mList.get(childPosition).last_seen));
        data.get(groupPosition).m2mList.get(childPosition).updateLabel=updated;
        setUpdated(groupPosition,childPosition);

        TextView stateLabel=(TextView)convertView.findViewById(R.id.State);
        stateLabel.setTag(String.valueOf(groupPosition)+","+String.valueOf(childPosition));
        data.get(groupPosition).m2mList.get(childPosition).stateLabel=stateLabel;
        setState(groupPosition,childPosition);
        return convertView;
    }

    @Override
    public int getChildrenCount(int groupPosition) {
        return groups.get(groupPosition).m2mList.size();
    }

    @Override
    public Object getGroup(int groupPosition) {
        return groups.get(groupPosition);
    }

    @Override
    public int getGroupCount() {
        return groups.size();
    }

    @Override
    public void onGroupCollapsed(int groupPosition) {
        super.onGroupCollapsed(groupPosition);
    }

    @Override
    public void onGroupExpanded(int groupPosition) {
        super.onGroupExpanded(groupPosition);
    }

    @Override
    public long getGroupId(int groupPosition) {
        return 0;
    }

    @Override
    public View getGroupView(int groupPosition, boolean isExpanded,View convertView, ViewGroup parent) {
        if (convertView == null) {
            convertView = inflater.inflate(R.layout.listgroup, null);
        }
        areas group = (areas) getGroup(groupPosition);
        ((CheckedTextView) convertView).setText(group.name);
        ((CheckedTextView) convertView).setChecked(isExpanded);
        return convertView;
    }

    @Override
    public boolean hasStableIds() {
        return false;
    }

    @Override
    public boolean isChildSelectable(int groupPosition, int childPosition) {
        return false;
    }



    public void showPic(Integer gid,Integer cid) {
        setPicSize(gid, cid, 1280, 720);
    }

    public void closePic(Integer gid, Integer cid) {
        setPicSize(gid, cid, 0, 0);
    }

    private void setPicSize(Integer gid, Integer cid, int width, int height) {
        ImageView webcam_pic=data.get(gid).m2mList.get(cid).webcam_pic;
        ViewGroup.LayoutParams params = webcam_pic.getLayoutParams();
        if(params.width!=width || params.height!=height) {
            params.width = width;
            params.height = height;
            webcam_pic.setLayoutParams(params);
        };
    }

    public boolean isPicOpen(Integer gid, Integer cid) {
        return data.get(gid).m2mList.get(cid).webcam_on;
    }

    public void setState(Integer gid, Integer cid){
        TextView label=data.get(gid).m2mList.get(cid).stateLabel;
        String textversion="Status: ";
        if(data.get(gid).m2mList.get(cid).state==0){
            textversion+="No Movement";
        } else if(data.get(gid).m2mList.get(cid).state==1){
            textversion+="Movement";
        } else {
            textversion+="Error";
        }

        if(data.get(gid).m2mList.get(cid).detection==0){
            textversion+=", not protected";
        } else if(data.get(gid).m2mList.get(cid).detection==1){
            textversion+=", protected";
        } else if(data.get(gid).m2mList.get(cid).detection==2){
            textversion+=", premium protected";
        } else {
            textversion+="Error";
        }
        label.setText(textversion);

        // display it or not?
        ExpandableListView WebcamView = (ExpandableListView) ((MainActivity)(context)).findViewById(R.id.listScroller);
        int firstVis = WebcamView.getFirstVisiblePosition();
        int lastVis = WebcamView.getLastVisiblePosition();
        int count = lastVis - firstVis;
        for(int i=0;i<=count;i++) {
            View v = WebcamView.getChildAt(i);
            if (v != null) {
                long packedPosition = WebcamView.getExpandableListPosition(i + firstVis);
                int packedPositionType = ExpandableListView.getPackedPositionType(packedPosition);

                if (packedPositionType != ExpandableListView.PACKED_POSITION_TYPE_NULL) {
                    int groupPosition = ExpandableListView.getPackedPositionGroup(packedPosition);
                    if (packedPositionType == ExpandableListView.PACKED_POSITION_TYPE_CHILD) {
                        int childPosition = ExpandableListView.getPackedPositionChild(packedPosition);
                        if(groupPosition==gid && childPosition==cid) {

                            TextView vislabel;
                            vislabel = (TextView) v.findViewById(R.id.State);
                            vislabel.setText(textversion);
                        }
                    }
                }
            }
        }
    }

    public void setUpdated(Integer gid, Integer cid){
        TextView label=data.get(gid).m2mList.get(cid).updateLabel;
        String textversion="Last Ping: ";
        DateFormat sdf = new SimpleDateFormat("H:m:s");
        Date netDate = (new Date(data.get(gid).m2mList.get(cid).last_seen*1000));
        textversion+= sdf.format(netDate);
        label.setText(textversion);
    }

//    public void showpic(int gid, int cid) {
//        data.get(gid).m2mList.get(cid).webcam_pic.setImageBitmap(data.get(gid).m2mList.get(cid).last_img);
//    }
}
