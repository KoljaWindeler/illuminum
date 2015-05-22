package com.example.kolja.Illumino;


import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.drawable.BitmapDrawable;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.LayerDrawable;
import android.util.SparseArray;
import android.view.LayoutInflater;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseExpandableListAdapter;
import android.widget.CheckedTextView;
import android.widget.ExpandableListView;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.TextView;
import org.json.JSONException;
import org.json.JSONObject;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Date;

public class ListAdapter extends BaseExpandableListAdapter {
    Context context;                        // reference to the App
    private final SparseArray<areas> data;  // reference to all the data
    private ColorPicker cP_color;
    private ColorPicker cP_bw;

    // constructor has to be callen with references to app and data
    public ListAdapter (Activity act, SparseArray<areas> groups) {
        this.context = act;
        this.data = groups;
    }

    //////////// GENERIC METHODS ///////
    @Override
    public Object getChild(int groupPosition, int childPosition) {
        return data.get(groupPosition).m2mList.get(childPosition);
    }

    @Override
    public long getChildId(int groupPosition, int childPosition) {
        return 0;
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
    public long getGroupId(int groupPosition) {
        return 0;
    }

    @Override
    public boolean hasStableIds() {
        return false;
    }

    @Override
    public boolean isChildSelectable(int groupPosition, int childPosition) {
        return false;
    }
    //////////// GENERIC METHODS ///////

    @Override
    public View getChildView(int groupPosition, final int childPosition,boolean isLastChild, View convertView, ViewGroup parent) {
        // check if we have to create it
        if (convertView == null) {
            convertView = ((LayoutInflater)((MainActivity)context).getLayoutInflater()).inflate(R.layout.listentry, null);
        }

        ////////////////////////////////////////////////////////////////////////////////////////////////////
        /////////////////////////////////// BUTTONS ////////////////////////////////////////////////////////
        ////////////////////////////////////////////////////////////////////////////////////////////////////

        ///////// WEBCAM BUTTON /////////
        // button, there is no need to set our image here, we'll do that later when we check for the displayed image anyway
        ImageButton webcam_on_off = (ImageButton) convertView.findViewById(R.id.webcam_on_off);
        webcam_on_off.setTag(String.valueOf(groupPosition)+","+String.valueOf(childPosition));
        data.get(groupPosition).m2mList.get(childPosition).onOffButton=webcam_on_off;
        webcam_on_off.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String Tag=(String) v.getTag();         // get our gid and cid from the tag
                String[] TagArray=Tag.split(",");
                int gid=Integer.parseInt(TagArray[0]);
                int cid=Integer.parseInt(TagArray[1]);


                // close webcam if open
                if(isWebCamPicOpen(gid, cid)){
                    stop_webcam_view(((View) v.getParent()).findViewById(R.id.webcam_on_off));
                }

                // open webcam view
                else {
                    // close alert Log if open
                    if(isAlertLogOpen(gid, cid)){
                        stop_AlertLog_view(((View) v.getParent()).findViewById(R.id.alertlog_on_off));
                    }

                    // close color picker if open
                    if(isColorPickerOpen(gid,cid)){
                        stop_ColorPicker_view(((View) v.getParent()).findViewById(R.id.colorpicker_on_off));
                    }

                    // start us!
                    start_webcam_view(v);
                }
            }
        });
        ///////// WEBCAM BUTTON /////////

        ///////// COLOR PICKER BUTTON /////////
        ImageButton color_picker_on_off = (ImageButton) convertView.findViewById(R.id.colorpicker_on_off);
        color_picker_on_off.setTag(String.valueOf(groupPosition)+","+String.valueOf(childPosition));
        color_picker_on_off.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String Tag=(String) v.getTag();         // get our gid and cid from the tag
                String[] TagArray=Tag.split(",");
                int gid=Integer.parseInt(TagArray[0]);
                int cid=Integer.parseInt(TagArray[1]);


                // close colorpicker if open
                if(isColorPickerOpen(gid, cid)){
                    stop_ColorPicker_view(((View) v.getParent()).findViewById(R.id.colorpicker_on_off));
                }

                // open colorpicker view
                else {
                    // close alert Log if open
                    if(isAlertLogOpen(gid, cid)){
                        stop_AlertLog_view(((View) v.getParent()).findViewById(R.id.alertlog_on_off));
                    }

                    // close webcam if open
                    if(isWebCamPicOpen(gid,cid)){
                        stop_webcam_view(((View) v.getParent()).findViewById(R.id.webcam_on_off));
                    }

                    // start us!
                    start_ColorPicker_view(v);
                }
            }
        });
        ///////// COLOR PICKER BUTTON /////////

        ///////// ALERT LOG BUTTON /////////
        ImageButton alert_log_on_off = (ImageButton) convertView.findViewById(R.id.alertlog_on_off);
        alert_log_on_off.setTag(String.valueOf(groupPosition)+","+String.valueOf(childPosition));
        alert_log_on_off.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String Tag = (String) v.getTag();         // get our gid and cid from the tag
                String[] TagArray = Tag.split(",");
                int gid = Integer.parseInt(TagArray[0]);
                int cid = Integer.parseInt(TagArray[1]);


                // close alert log if open
                if (isAlertLogOpen(gid, cid)) {
                    stop_AlertLog_view(((View) v.getParent()).findViewById(R.id.alertlog_on_off));
                }

                // open colorpicker view
                else {
                    // close webcam view if open
                    if (isColorPickerOpen(gid, cid)) {
                        stop_ColorPicker_view(((View) v.getParent()).findViewById(R.id.colorpicker_on_off));
                    }

                    // close webcam if open
                    if (isWebCamPicOpen(gid, cid)) {
                        stop_webcam_view(((View) v.getParent()).findViewById(R.id.webcam_on_off));
                    }

                    // start us!
                    start_AlertLog_view(v);

                }
            }
        });
        ///////// ALERT LOG BUTTON /////////

        ////////////////////////////////////////////////////////////////////////////////////////////////////
        /////////////////////////////////// BUTTONS ////////////////////////////////////////////////////////
        ////////////////////////////////////////////////////////////////////////////////////////////////////

        ////////////////////////////////////////////////////////////////////////////////////////////////////
        /////////////////////////////////// Flex View //////////////////////////////////////////////////////
        ////////////////////////////////////////////////////////////////////////////////////////////////////

        ////////////////////////////////
        ///////// webcam image /////////
        ////////////////////////////////
        if(isWebCamPicOpen(groupPosition, childPosition)){ // in this case this is more like a: "should it be open?"
            webcam_on_off.setImageResource(R.drawable.red);
            ImageView webcam_pic=(ImageView)convertView.findViewById(R.id.webcam_picture_in_single_view);

            if(webcam_pic==null) {
                // show it if
                showPic(convertView, groupPosition, childPosition);
                // grab it again, showPic will destory every view and ours was null anyway
                webcam_pic = (ImageView) convertView.findViewById(R.id.webcam_picture_in_single_view);

                // save it to the queue, supprising that this works and is able to distinguish between two lines of the same type
                data.get(groupPosition).m2mList.get(childPosition).webcam_pic=webcam_pic;
            };

            // we need to keep this here to update every picture with new bitmaps we've received while this was in the background
            // if we have a stored picture, even if it might be a little older, display it. Otherwise show the simple loading picture
            if(data.get(groupPosition).m2mList.get(childPosition).last_img!=null) {
                webcam_pic.setImageBitmap(data.get(groupPosition).m2mList.get(childPosition).last_img);
            } else {
                webcam_pic.setImageBitmap(BitmapFactory.decodeResource(convertView.getContext().getResources(), R.drawable.webcam));
            }
        }
        // just make sure that the webcam picture is really closed
        else {
            webcam_on_off.setImageResource(R.drawable.livestream_icon_v01);
            if(convertView.findViewById(R.id.webcam_picture_in_single_view)!=null) {
                closePic(convertView, groupPosition, childPosition);
            };
        }
        ////////////////////////////////
        ///////// webcam image /////////
        ////////////////////////////////

        ////////////////////////////////
        ///////// color picker /////////
        ////////////////////////////////
        if(isColorPickerOpen(groupPosition,childPosition)){ // in this case this is more like a: "should it be open?"
            color_picker_on_off.setImageResource(R.drawable.red);
            LinearLayout colorPickerLayout = (LinearLayout) convertView.findViewById(R.id.colorpicker_in_single_view);
            if(colorPickerLayout==null){
                // show it if
                showColorPicker(convertView, groupPosition, childPosition);
                colorPickerLayout = (LinearLayout) convertView.findViewById(R.id.colorpicker_in_single_view);
            }
            // do something like drag it into the right position
        }

        else {
            color_picker_on_off.setImageResource(R.drawable.lightcontrol_icon_v01);
            if(convertView.findViewById(R.id.colorpicker_in_single_view)!=null){
                closeColorPicker(convertView,groupPosition,childPosition);
            }
        }
        ////////////////////////////////
        ///////// color picker /////////
        ////////////////////////////////

        ////////////////////////////////
        ///////// AlertLog /////////////
        ////////////////////////////////
        if(isAlertLogOpen(groupPosition,childPosition)){    // in this case this is more like a: "should it be open?"
            alert_log_on_off.setImageResource(R.drawable.red);
            LinearLayout colorPickerLayout = (LinearLayout) convertView.findViewById(R.id.alertlog_in_single_view);
            if(colorPickerLayout==null){
                // show it if
                showAlertLog(convertView, groupPosition, childPosition);
                colorPickerLayout = (LinearLayout) convertView.findViewById(R.id.alertlog_in_single_view);
            }
            // do something like drag it into the right position
        }

        else {
            alert_log_on_off.setImageResource(R.drawable.alarms_icon_v01);
            if(convertView.findViewById(R.id.alertlog_in_single_view)!=null){
                closeAlertLog(convertView,groupPosition,childPosition);
            }
        }
        ////////////////////////////////
        ///////// AlertLog /////////////
        ////////////////////////////////

        ////////////////////////////////////////////////////////////////////////////////////////////////////
        /////////////////////////////////// Flex View //////////////////////////////////////////////////////
        ////////////////////////////////////////////////////////////////////////////////////////////////////

        ////////////////////////////////////////////////////////////////////////////////////////////////////
        /////////////////////////////////// Text Field /////////////////////////////////////////////////////
        ////////////////////////////////////////////////////////////////////////////////////////////////////

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

        ////////////////////////////////////////////////////////////////////////////////////////////////////
        /////////////////////////////////// Text Field /////////////////////////////////////////////////////
        ////////////////////////////////////////////////////////////////////////////////////////////////////

        return convertView;
    }

    // start the alert log view
    // arguement is the view on the button
    private void start_AlertLog_view(View v) {
        String Tag=(String) v.getTag();         // get our gid and cid from the tag
        String[] TagArray=Tag.split(",");
        int gid=Integer.parseInt(TagArray[0]);
        int cid=Integer.parseInt(TagArray[1]);

        if(!isAlertLogOpen(gid, cid)){
            data.get(gid).m2mList.get(cid).alertlog_on=true;
            ((ImageButton) v).setImageResource(R.drawable.red);
            showAlertLog((View) v.getParent().getParent().getParent(), gid, cid);
        }
    }

    // stop the alert log view
    // arguement is the view on the button
    private void stop_AlertLog_view(View v) {
        String Tag=(String) v.getTag();         // get our gid and cid from the tag
        String[] TagArray=Tag.split(",");
        int gid=Integer.parseInt(TagArray[0]);
        int cid=Integer.parseInt(TagArray[1]);

        // lookup if the picture is displayed, in this case, close it and send stop message
        if(isAlertLogOpen(gid, cid)){
            ((ImageButton) v).setImageResource(R.drawable.alarms_icon_v01);
            closeAlertLog((View) v.getParent().getParent().getParent(), gid, cid);
            data.get(gid).m2mList.get(cid).alertlog_on=false;
        }
    }

    // arguement is the view on the button
    private void start_ColorPicker_view(View v) {
        String Tag=(String) v.getTag();         // get our gid and cid from the tag
        String[] TagArray=Tag.split(",");
        int gid=Integer.parseInt(TagArray[0]);
        int cid=Integer.parseInt(TagArray[1]);

        if(!isColorPickerOpen(gid, cid)){
            data.get(gid).m2mList.get(cid).colorpicker_on=true;
            ((ImageButton) v).setImageResource(R.drawable.red);
            showColorPicker((View) v.getParent().getParent().getParent(), gid, cid);
        }
    }

    // arguement is the view on the button
    private void stop_ColorPicker_view(View v) {
        String Tag=(String) v.getTag();         // get our gid and cid from the tag
        String[] TagArray=Tag.split(",");
        int gid=Integer.parseInt(TagArray[0]);
        int cid=Integer.parseInt(TagArray[1]);

        // lookup if the picture is displayed, in this case, close it and send stop message
        if(isColorPickerOpen(gid, cid)){
            ((ImageButton) v).setImageResource(R.drawable.lightcontrol_icon_v01);
            closeColorPicker((View) v.getParent().getParent().getParent(), gid, cid);
            data.get(gid).m2mList.get(cid).colorpicker_on=false;
        }
    }

    // starts the webcam view, the argument V has to be the start stop button
    private void start_webcam_view(View v) {
        String Tag=(String) v.getTag();         // get our gid and cid from the tag
        String[] TagArray=Tag.split(",");
        int gid=Integer.parseInt(TagArray[0]);
        int cid=Integer.parseInt(TagArray[1]);

        // lookup if the picture is displayed, in this case, close it and send stop message
        if(!isWebCamPicOpen(gid, cid)){
            ((ImageButton) v).setImageResource(R.drawable.red);
            showPic((View) v.getParent().getParent().getParent(), gid, cid);
            if(data.get(gid).m2mList.get(cid).last_img!=null) {
                data.get(gid).m2mList.get(cid).webcam_pic.setImageBitmap(data.get(gid).m2mList.get(cid).last_img);
            } else {
                data.get(gid).m2mList.get(cid).webcam_pic.setImageBitmap(BitmapFactory.decodeResource(v.getContext().getResources(), R.drawable.webcam));
            }
            data.get(gid).m2mList.get(cid).webcam_on=true;
            // set interval to 1 fps, this will be send to the Server below
            send_webcam_interval(1,gid,cid);
        }
    }

    // arguement is the view on the button
    private void stop_webcam_view(View v) {
        String Tag=(String) v.getTag();         // get our gid and cid from the tag
        String[] TagArray=Tag.split(",");
        int gid=Integer.parseInt(TagArray[0]);
        int cid=Integer.parseInt(TagArray[1]);

        // lookup if the picture is displayed, in this case, close it and send stop message
        if(isWebCamPicOpen(gid, cid)){
            ((ImageButton) v).setImageResource(R.drawable.livestream_icon_v01);
            closePic((View) v.getParent().getParent().getParent(), gid, cid);
            data.get(gid).m2mList.get(cid).webcam_on=false;
            // set interval to 0, this will be send to the Server below
            send_webcam_interval(0, gid, cid);
        }
    }

    // helper function for open and close the webcam view -> tell it the server
    private void send_webcam_interval(float interval, int gid, int cid) {
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

    // helper function for setting the color
    private void send_color(int gid, int cid) {
        // fire message to the server, via our Service
        JSONObject object_send = new JSONObject();
        try {
            int b = Color.blue(cP_bw.getColor(data.get(gid).m2mList.get(cid).brightness_pos));
            int c = cP_color.getColor(data.get(gid).m2mList.get(cid).color_pos);

            object_send.put("cmd", "set_color");
            object_send.put("mid", data.get(gid).m2mList.get(cid).mid);
            object_send.put("r", (int)(((float)Color.red(c))  /255f*100f*b/255f)); // rgb in rage of 0-100 for the light controll to do the half-log trick
            object_send.put("g", (int)(((float)Color.green(c))/255f*100f*b/255f));
            object_send.put("b", (int)(((float)Color.blue(c)) /255f*100f*b/255f));
            object_send.put("brightness_pos", data.get(gid).m2mList.get(cid).brightness_pos);
            object_send.put("color_pos", data.get(gid).m2mList.get(cid).color_pos);


            Intent send_intent = new Intent(bg_service.SENDER);
            send_intent.putExtra(s_ws.TYPE, s_ws.APP2SERVER);
            send_intent.putExtra(s_ws.PAYLOAD, object_send.toString());
            ((MainActivity)context).sendBroadcast(send_intent);
        } catch (JSONException e) {
            e.printStackTrace();
        }
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


    ///////// WEBCAM ////////////
    public void showPic(View v, Integer gid, Integer cid) {
        View inserter=insertViewInWorker(R.layout.show_webcam_pic,v,1280,720);
        if(inserter!=null) {
            // grab out webcam_picture
            ImageView webcam_pic;
            webcam_pic = (ImageView) inserter.findViewById(R.id.webcam_picture_in_single_view);
            webcam_pic.setTag(String.valueOf(gid) + "," + String.valueOf(cid));
            // save? it for later <- i don't think this works
            data.get(gid).m2mList.get(cid).webcam_pic = webcam_pic;
        }
        data.get(gid).m2mList.get(cid).webcam_on=true;
    }

    public void closePic(View v, Integer gid, Integer cid) {
        removeAllViewsFromWorker(v);
        data.get(gid).m2mList.get(cid).webcam_on=false;
    }
    ///////// WEBCAM ////////////

    ///////// COLOR PICKER ////////////
    private void showColorPicker(View v, int gid, int cid) {
        data.get(gid).m2mList.get(cid).colorpicker_on=true;
        insertViewInWorker(R.layout.show_color_picker,v, LinearLayout.LayoutParams.WRAP_CONTENT,LinearLayout.LayoutParams.WRAP_CONTENT); // TODO FILL_PARENT,WRAP_CONTENT

        SeekBar ColorView=((SeekBar)v.findViewById(R.id.Color));
        cP_color = new ColorPicker(v);
        cP_color.prepare(ColorView, 0, false);
        cP_color.generate_bitmap();
        LayerDrawable background = new LayerDrawable(new Drawable[]{new BitmapDrawable(cP_color.mBitmap)});
        ColorView.setBackground(background);
        ColorView.setTag(String.valueOf(gid) + "," + String.valueOf(cid));
        ColorView.setProgress(data.get(gid).m2mList.get(cid).color_pos);
        ColorView.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            @Override
            public void onProgressChanged(SeekBar arg0, int arg1, boolean arg2) {
                String Tag = (String) arg0.getTag();         // get our gid and cid from the tag
                String[] TagArray = Tag.split(",");
                int gid = Integer.parseInt(TagArray[0]);
                int cid = Integer.parseInt(TagArray[1]);
                data.get(gid).m2mList.get(cid).color_pos = arg1;
                send_color(gid,cid);
            }

            @Override
            public void onStartTrackingTouch(SeekBar seekBar) {

            }
            @Override
            public void onStopTrackingTouch(SeekBar seekBar) {

            }
        });

        SeekBar BlackWhiteView=((SeekBar)v.findViewById(R.id.BlackWhite));
        cP_bw = new ColorPicker(v);
        cP_bw.prepare(BlackWhiteView, 0, true);
        cP_bw.generate_bitmap();
        background = new LayerDrawable(new Drawable[]{new BitmapDrawable(cP_bw.mBitmap)});
        BlackWhiteView.setBackground(background);
        BlackWhiteView.setTag(String.valueOf(gid) + "," + String.valueOf(cid));
        BlackWhiteView.setProgress(data.get(gid).m2mList.get(cid).brightness_pos);
        BlackWhiteView.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            @Override
            public void onProgressChanged(SeekBar arg0, int arg1, boolean arg2) {


                String Tag = (String) arg0.getTag();         // get our gid and cid from the tag
                String[] TagArray = Tag.split(",");
                int gid = Integer.parseInt(TagArray[0]);
                int cid = Integer.parseInt(TagArray[1]);
                data.get(gid).m2mList.get(cid).brightness_pos = arg1;
                send_color(gid,cid);
            }

            @Override
            public void onStartTrackingTouch(SeekBar seekBar) {

            }
            @Override
            public void onStopTrackingTouch(SeekBar seekBar) {

            }
        });

    }

    public void closeColorPicker(View v, Integer gid, Integer cid) {
        removeAllViewsFromWorker(v);
        data.get(gid).m2mList.get(cid).colorpicker_on=false;
    }
    ///////// COLOR PICKER ////////////

    ///////// ALERT LOG ////////////
    private void showAlertLog(View v, int gid, int cid) {
        data.get(gid).m2mList.get(cid).alertlog_on=true;
        insertViewInWorker(R.layout.show_alert_log,v, LinearLayout.LayoutParams.WRAP_CONTENT,LinearLayout.LayoutParams.WRAP_CONTENT); // TODO FILL_PARENT,WRAP_CONTENT
    }

    public void closeAlertLog(View v, Integer gid, Integer cid) {
        removeAllViewsFromWorker(v);
        data.get(gid).m2mList.get(cid).alertlog_on=false;
    }
    ///////// ALERT LOG ////////////

    ///////// GENERIC ////////////
    private void removeAllViewsFromWorker(View v) {
        LinearLayout insertPoint = (LinearLayout) v.findViewById(R.id.work);
        if (insertPoint != null) {
            insertPoint.removeAllViews();
        }
    }

    private View insertViewInWorker(int this_layout, View v, int width, int height){
        LinearLayout insertPoint = (LinearLayout) v.findViewById(R.id.work);
        if(insertPoint!=null) {
            // remove all
            insertPoint.removeAllViews();
            // inflate our webcamview
            LayoutInflater vi = (LayoutInflater) context.getApplicationContext().getSystemService(Context.LAYOUT_INFLATER_SERVICE);
            View inserter = vi.inflate(this_layout, null);
            // add the view to our inserPoint
            LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(width, height);
            params.topMargin=60; //?
            insertPoint.addView(inserter, 0,params );
            return inserter;
        }
        return null;
    }
    ///////// GENERIC ////////////

    public boolean isWebCamPicOpen(Integer gid, Integer cid) {
        return data.get(gid).m2mList.get(cid).webcam_on;
    }

    private boolean isColorPickerOpen(int gid, int cid) {
        return data.get(gid).m2mList.get(cid).colorpicker_on;
    }

    private boolean isAlertLogOpen(int gid, int cid) {
        return data.get(gid).m2mList.get(cid).alertlog_on;
    }

    public void setState(Integer gid, Integer cid){
        // build the message
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

        // display it or not? TODO: THIS NEEDS TO BE TESTED, IF IT WORKS INSTALL IT in setUPdate
        ExpandableListView WebcamView = (ExpandableListView) ((MainActivity)(context)).findViewById(R.id.listScroller);
        View v=((MainActivity)context).getView_ifVisible(gid,cid,WebcamView);
        if(v!=null){
            TextView vislabel;
            vislabel = (TextView) v.findViewById(R.id.State);
            vislabel.setText(textversion);
        }

//        int firstVis = WebcamView.getFirstVisiblePosition();
//        int lastVis = WebcamView.getLastVisiblePosition();
//        int count = lastVis - firstVis;
//        for(int i=0;i<=count;i++) {
//            View v = WebcamView.getChildAt(i);
//            if (v != null) {
//                long packedPosition = WebcamView.getExpandableListPosition(i + firstVis);
//                int packedPositionType = ExpandableListView.getPackedPositionType(packedPosition);
//
//                if (packedPositionType != ExpandableListView.PACKED_POSITION_TYPE_NULL) {
//                    int groupPosition = ExpandableListView.getPackedPositionGroup(packedPosition);
//                    if (packedPositionType == ExpandableListView.PACKED_POSITION_TYPE_CHILD) {
//                        int childPosition = ExpandableListView.getPackedPositionChild(packedPosition);
//                        if(groupPosition==gid && childPosition==cid) {
//
//                            TextView vislabel;
//                            vislabel = (TextView) v.findViewById(R.id.State);
//                            vislabel.setText(textversion);
//                        }
//                    }
//                }
//            }
//        }
    }

    public void setUpdated(Integer gid, Integer cid){
        TextView label=data.get(gid).m2mList.get(cid).updateLabel;
        setUpdated(gid,cid,label);
    }

    public void setUpdated(Integer gid, Integer cid, TextView label){
        String textversion="Last Ping: ";
        DateFormat sdf = new SimpleDateFormat("HH:mm");
        Date netDate = (new Date(data.get(gid).m2mList.get(cid).last_seen*1000));
        textversion+= sdf.format(netDate);
        label.setText(textversion);
    }


}
