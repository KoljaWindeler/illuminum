package com.example.kolja.Illumino;

/**
 * Created by kolja on 5/19/15.
 */
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;

import java.util.ArrayList;
import java.util.List;

public class areas {

    public String name;
    public Bitmap symbol;
    public String detection;
    public final List<m2m_container> m2mList = new ArrayList<m2m_container>();

    public areas(Context ct,String AreaName, Integer type) {
        this.name = AreaName;
        if(type==1){
            symbol=BitmapFactory.decodeResource(ct.getResources(), R.drawable.home);
        } else {
            symbol=BitmapFactory.decodeResource(ct.getResources(), R.drawable.castle);
        }
    }

}