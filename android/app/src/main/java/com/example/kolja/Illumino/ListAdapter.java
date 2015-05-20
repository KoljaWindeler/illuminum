package com.example.kolja.Illumino;


import android.app.ActionBar;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseExpandableListAdapter;
import android.widget.CheckedTextView;
import android.widget.ExpandableListView;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.util.SparseArray;

import org.json.JSONException;
import org.json.JSONObject;

import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Date;

public class ListAdapter extends BaseExpandableListAdapter {
    Context context;                        // reference to the App
    private final SparseArray<areas> data;  // reference to all the data

    // constructor has to be callen with references to app and data
    public ListAdapter (Activity act, SparseArray<areas> groups) {
        this.context = act;
        this.data = groups;
    }

    @Override
    public Object getChild(int groupPosition, int childPosition) {
        return data.get(groupPosition).m2mList.get(childPosition);
    }

    @Override
    public long getChildId(int groupPosition, int childPosition) {
        return 0;
    }

    @Override
    public View getChildView(int groupPosition, final int childPosition,boolean isLastChild, View convertView, ViewGroup parent) {
        // check if we have to create it
        if (convertView == null) {
            convertView = ((LayoutInflater)((MainActivity)context).getLayoutInflater()).inflate(R.layout.listentry, null);
        }

        // button, there is no need to set our image here, we'll do that later when we check for the displayed image anyway
        ImageButton webcam_on_off = (ImageButton) convertView.findViewById(R.id.webcam_on_off);
        webcam_on_off.setTag(String.valueOf(groupPosition)+","+String.valueOf(childPosition));
        data.get(groupPosition).m2mList.get(childPosition).onOffButton=webcam_on_off;
        webcam_on_off.setOnClickListener(new View.OnClickListener() {

            @Override
            public void onClick(View v) {
                int interval=0;                         // speed of image updates
                String Tag=(String) v.getTag();         // get our gid and cid from the tag
                String[] TagArray=Tag.split(",");
                int gid=Integer.parseInt(TagArray[0]);
                int cid=Integer.parseInt(TagArray[1]);

                // lookup if the picture is displayed, in this case, close it and send stop message
                if(isPicOpen(gid,cid)){
                    ((ImageButton) v).setImageResource(R.drawable.livestream_icon_v01);
                    closePic((View)v.getParent().getParent().getParent(),gid,cid);
                    data.get(gid).m2mList.get(cid).webcam_on=false;
                    // set interval to 0, this will be send to the Server below
                    interval=0;
                }
                // else it is not shown, therefor show the picture and see if you have already an old picture we can show
                else {
                    ((ImageButton) v).setImageResource(R.drawable.red);
                    showPic((View)v.getParent().getParent().getParent(), gid,cid);
                    if(data.get(gid).m2mList.get(cid).last_img!=null) {
                        data.get(gid).m2mList.get(cid).webcam_pic.setImageBitmap(data.get(gid).m2mList.get(cid).last_img);
                    } else {
                        data.get(gid).m2mList.get(cid).webcam_pic.setImageBitmap(BitmapFactory.decodeResource(v.getContext().getResources(), R.drawable.webcam));
                    }
                    data.get(gid).m2mList.get(cid).webcam_on=true;
                    // set interval to 1 fps, this will be send to the Server below
                    interval=1;
                }

                // fire message to the server, via our Service
                JSONObject object_send = new JSONObject();
                try {
                    object_send.put("cmd", "set_interval");
                    object_send.put("mid", data.get(gid).m2mList.get(cid).mid);
                    object_send.put("interval", interval);

                    Intent send_intent = new Intent(bg_service.SENDER);
                    send_intent.putExtra(s_ws.TYPE, s_ws.APP2SERVER);
                    send_intent.putExtra(s_ws.PAYLOAD, object_send.toString());
                    ((MainActivity)context).sendBroadcast(send_intent);
                } catch (JSONException e) {
                    e.printStackTrace();
                }
            }
        });

        //// webcam image /////
        if(isPicOpen(groupPosition,childPosition)){ // in this case this is more like a: "should it be open?"
            webcam_on_off.setImageResource(R.drawable.red);
            ImageView webcam_pic=(ImageView)convertView.findViewById(R.id.webcam_picture_in_single_view);

            if(webcam_pic==null) {
                // show it if
                showPic(convertView, groupPosition, childPosition);
                // grab it again, showPic will destory every view and ours was null anyway
                webcam_pic = (ImageView) convertView.findViewById(R.id.webcam_picture_in_single_view);
                webcam_pic.setTag(String.valueOf(groupPosition)+","+String.valueOf(childPosition));

                // save it to the queue, supprising that this works and is able to distinguish between two lines of the same type
                data.get(groupPosition).m2mList.get(childPosition).webcam_pic=webcam_pic;
            };

            // if we have a stored picture, even if it might be a little older, display it. Otherwise show the simple loading picture
            if(data.get(groupPosition).m2mList.get(childPosition).last_img!=null) {
                webcam_pic.setImageBitmap(data.get(groupPosition).m2mList.get(childPosition).last_img);
            } else {
                webcam_pic.setImageBitmap(BitmapFactory.decodeResource(convertView.getContext().getResources(), R.drawable.webcam));
            }
        }
        // just make sure that the picture is really closed
        else {
            webcam_on_off.setImageResource(R.drawable.livestream_icon_v01);
            if(convertView.findViewById(R.id.webcam_picture_in_single_view)!=null) {
                closePic(convertView, groupPosition, childPosition);
            };
        }

        //// text Alias ////
        TextView alias=(TextView)convertView.findViewById(R.id.Alias);
        alias.setTag(String.valueOf(groupPosition)+","+String.valueOf(childPosition));
        alias.setText(data.get(groupPosition).m2mList.get(childPosition).alias);
        data.get(groupPosition).m2mList.get(childPosition).aliasLabel=alias;

        //// text last updated ////
        TextView updated=(TextView)convertView.findViewById(R.id.LastUpdated);
        updated.setTag(String.valueOf(groupPosition) + "," + String.valueOf(childPosition));
        updated.setText(String.valueOf(data.get(groupPosition).m2mList.get(childPosition).last_seen));
        data.get(groupPosition).m2mList.get(childPosition).updateLabel=updated;
        setUpdated(groupPosition,childPosition);

        //// text state ////
        TextView stateLabel=(TextView)convertView.findViewById(R.id.State);
        stateLabel.setTag(String.valueOf(groupPosition)+","+String.valueOf(childPosition));
        data.get(groupPosition).m2mList.get(childPosition).stateLabel=stateLabel;
        setState(groupPosition,childPosition);


        return convertView;
    }

    @Override
    public int getChildrenCount(int groupPosition) {
        return data.get(groupPosition).m2mList.size();
    }

    @Override
    public Object getGroup(int groupPosition) {
        return data.get(groupPosition);
    }

    @Override
    public int getGroupCount() {
        return data.size();
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
            convertView = ((LayoutInflater)((MainActivity)context).getLayoutInflater()).inflate(R.layout.listgroup, null);
        }
        areas group = (areas) getGroup(groupPosition);
        ((TextView)convertView.findViewById(R.id.area_name)).setText(group.name);
        ((CheckedTextView)convertView.findViewById(R.id.opener)).setChecked(isExpanded);
        ((ImageView)convertView.findViewById(R.id.area_symbol)).setImageBitmap(group.symbol);
        if(data.get(groupPosition).m2mList.get(0).detection==0) {
            ((TextView) convertView.findViewById(R.id.area_detection)).setText("Not protected");
        } else {
            ((TextView) convertView.findViewById(R.id.area_detection)).setText("Protected");
        }
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



    public void showPic(View v, Integer gid, Integer cid) {
        setPicSize(v, gid, cid, 1280, 720);
        data.get(gid).m2mList.get(cid).webcam_on=true;
    }

    public void closePic(View v, Integer gid, Integer cid) {
        setPicSize(v, gid, cid, 0, 0);
        data.get(gid).m2mList.get(cid).webcam_on=false;
    }

    private void setPicSize(View v, Integer gid, Integer cid, int width, int height) {
        LinearLayout insertPoint = (LinearLayout) v.findViewById(R.id.work);
        if(insertPoint!=null) {
            if (width == 0 && height == 0) {
                insertPoint.removeAllViews();
            } else {
                // remove all
                insertPoint.removeAllViews();
                // inflate our webcamview
                LayoutInflater vi = (LayoutInflater) context.getApplicationContext().getSystemService(Context.LAYOUT_INFLATER_SERVICE);
                View inserter = vi.inflate(R.layout.show_webcam_pic, null);
                // grab out webcam_picture
                ImageView webcam_pic;
                webcam_pic = (ImageView) inserter.findViewById(R.id.webcam_picture_in_single_view);
                // add the view to our inserPoint
                LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(width, height);
                params.topMargin=60; //?
                insertPoint.addView(inserter, 0,params );
                // save? it for later <- i don't think this works
                data.get(gid).m2mList.get(cid).webcam_pic = webcam_pic;
            }
        }
        //webcam_pic.setImageBitmap(Bitmap.createScaledBitmap(decodedByte, width, height, false)); //TODO


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
        setUpdated(gid,cid,label);
    }

    public void setUpdated(Integer gid, Integer cid, TextView label){
        String textversion="Last Ping: ";
        DateFormat sdf = new SimpleDateFormat("HH:mm:ss");
        Date netDate = (new Date(data.get(gid).m2mList.get(cid).last_seen*1000));
        textversion+= sdf.format(netDate);
        label.setText(textversion);
    }

//    public void showpic(int gid, int cid) {
//        data.get(gid).m2mList.get(cid).webcam_pic.setImageBitmap(data.get(gid).m2mList.get(cid).last_img);
//    }
}
