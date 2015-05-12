package com.example.kolja.alert_app;


import android.app.Activity;
import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.View.OnClickListener;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.SeekBar;
import android.widget.SeekBar.OnSeekBarChangeListener;
import android.widget.TextView;

public class ListAdapter extends ArrayAdapter<ListContainer> {
    Context context;
    int layoutResourceId;
    ListContainer data[]=null;
    TextView text_status[]=new TextView[13];
    ImageButton image_status[]=new ImageButton[13];
    SeekBar seek_status[]=new SeekBar[13];



    public ListAdapter (Context context, int layoutResourceId, ListContainer[] data) {
        super(context, layoutResourceId, data);
        this.layoutResourceId = layoutResourceId;
        this.context = context;
        this.data = data;
    }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
        View row = convertView;
        ListInfoHolder holder = new ListInfoHolder();

        LayoutInflater inflater = ((Activity)context).getLayoutInflater();
        row = inflater.inflate(layoutResourceId, parent, false);

        //// birne ////
        /*holder.auto_on_off=(ImageButton)row.findViewById(R.id.auto_on_off);
        // magic save it
        image_status[position]=(ImageButton)row.findViewById(R.id.auto_on_off);
        if(data[position].auto_modus){
            holder.auto_on_off.setImageResource(R.drawable.gluehbirne);
        } else {
            holder.auto_on_off.setImageResource(R.drawable.gluehbirne_gray);
        }
        holder.auto_on_off.setTag(position);
        holder.auto_on_off.setOnClickListener(new OnClickListener() {

            @Override
            public void onClick(View v) {
                if(data[(Integer) v.getTag()].auto_modus){
                    data[(Integer) v.getTag()].auto_modus=false;
                    ((ImageButton) v).setImageResource(R.drawable.gluehbirne_gray);
                    ((LightControllAppActivity)context).cmd_set_mode_auto(data[(Integer)v.getTag()].pin,false);
                } else {
                    seek_status[(Integer) v.getTag()].setProgress(0);
                    data[(Integer) v.getTag()].auto_modus=true;
                    data[(Integer) v.getTag()].current_value=0;
                    ((ImageButton) v).setImageResource(R.drawable.gluehbirne);
                    ((LightControllAppActivity)context).cmd_set_mode_auto(data[(Integer)v.getTag()].pin,true);
                    text_status[(Integer) v.getTag()].setText(data[(Integer) v.getTag()].name+": AutoMode");
                }

            }
        });
        */
        //// text ////
        holder.current_state=(TextView)row.findViewById(R.id.current_state);
        holder.current_state.setTag(position);
        if(data[position].auto_modus){
            holder.current_state.setText(data[position].name+": AutoMode");
        } else {
            holder.current_state.setText(data[position].name+": "+String.valueOf(data[position].current_value)+"%");
        };
        /*
        // magic save it
        text_status[position]=(TextView)row.findViewById(R.id.current_state);


        //// seeker ////
        holder.seeker=(SeekBar)row.findViewById(R.id.seeker);
        holder.seeker.setProgress(data[position].current_value);
        holder.seeker.setTag(position);
        holder.seeker.setProgress(data[position].current_value);
        seek_status[position]=(SeekBar)row.findViewById(R.id.seeker);
        holder.seeker.setOnSeekBarChangeListener(new OnSeekBarChangeListener() {

            @Override
            public void onStopTrackingTouch(SeekBar seekBar) {
                // TODO Auto-generated method stub
                ((LightControllAppActivity)context).cmd_dimm_pin(data[(Integer)seekBar.getTag()].pin,seekBar.getProgress(),25,false);
                data[(Integer) seekBar.getTag()].current_value=seekBar.getProgress();
                text_status[(Integer) seekBar.getTag()].setText(data[(Integer) seekBar.getTag()].name+": "+String.valueOf(seekBar.getProgress())+"%");

            }

            @Override
            public void onStartTrackingTouch(SeekBar seekBar) {
                // TODO Auto-generated method stub

            }

            @Override
            public void onProgressChanged(SeekBar seekBar, int progress,
                                          boolean fromUser) {
                ((LightControllAppActivity)context).cmd_dimm_pin(data[(Integer)seekBar.getTag()].pin,progress,25,true);
                data[(Integer)seekBar.getTag()].current_value=seekBar.getProgress();
                text_status[(Integer) seekBar.getTag()].setText(data[(Integer) seekBar.getTag()].name+": "+String.valueOf(seekBar.getProgress())+"%");
                image_status[(Integer) seekBar.getTag()].setImageResource(R.drawable.gluehbirne_gray);
                data[(Integer) seekBar.getTag()].auto_modus=false;
                ((LightControllAppActivity)context).cmd_set_mode_auto(data[(Integer)seekBar.getTag()].pin,false);
            }
        });*/


        row.setTag(holder);
        return row;
    }

    static class ListInfoHolder
    {
        SeekBar seeker;
        ImageButton auto_on_off;
        TextView current_state;
    }



}
