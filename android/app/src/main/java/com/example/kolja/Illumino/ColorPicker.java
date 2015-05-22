package com.example.kolja.Illumino;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.view.View;
import android.widget.ImageView;
import android.widget.SeekBar;

/**
 * Created by kolja on 5/21/15.
 */
public class ColorPicker {
    private int width, height;
    private Paint mPaint;
    private Canvas mCanvas;
    public Bitmap mBitmap;
    private float mCurrentHue = 0;
    private int mCurrentX = 0, mCurrentY = 0;
    private int mCurrentColor, mDefaultColor;
    public final int[] mHueBarColors = new int[258];
    private float mScale;

    public ColorPicker(View listAdapter) {
        float scale = listAdapter.getContext().getResources().getDisplayMetrics().density;
        //px = dp_that_you_want * (scale / 160);
        mScale=scale/160;
    }


    public void prepare(SeekBar v, int color, boolean bw) {
        width = (int)(v.getLayoutParams().width);
        height = (int)(v.getLayoutParams().height);



        float[] hsv = new float[3];
        Color.colorToHSV(color, hsv);
        mCurrentHue = hsv[0];


        mCurrentColor = color;

        if(!bw) {
            // Initialize the colors of the hue slider bar
            int index = 0;
            for (float i = 0; i < 256; i += 256 / 42) // Red (#f00) to pink (#f0f)
            {
                mHueBarColors[index] = Color.rgb(255, 0, (int) i);
                index++;
            }
            for (float i = 0; i < 256; i += 256 / 42) // Pink (#f0f) to blue
            // (#00f)
            {
                mHueBarColors[index] = Color.rgb(255 - (int) i, 0, 255);
                index++;
            }
            for (float i = 0; i < 256; i += 256 / 42) // Blue (#00f) to light
            // blue (#0ff)
            {
                mHueBarColors[index] = Color.rgb(0, (int) i, 255);
                index++;
            }
            for (float i = 0; i < 256; i += 256 / 42) // Light blue (#0ff) to green (#0f0)
            {
                mHueBarColors[index] = Color.rgb(0, 255, 255 - (int) i);
                index++;
            }
            for (float i = 0; i < 256; i += 256 / 42) // Green (#0f0) to yellow (#ff0)
            {
                mHueBarColors[index] = Color.rgb((int) i, 255, 0);
                index++;
            }
            for (float i = 0; i < 256; i += 256 / 42) // Yellow (#ff0) to red (#f00)
            {
                mHueBarColors[index] = Color.rgb(255, 255 - (int) i, 0);
                index++;
            }
            mHueBarColors[0] = Color.rgb(255, 255 ,255);

        } else {
            for(int i=0;i<256;i++){
                mHueBarColors[i]=Color.rgb(i,i,i);
            }
            for(int i=256;i<mHueBarColors.length;i++){
                mHueBarColors[i]=Color.rgb(255,255,255);
            }
        }
    }

    public void generate_bitmap(){
        // Initializes the Paint that will draw the View
        mPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        mBitmap = Bitmap.createBitmap(width, height, Bitmap.Config.RGB_565);
        mCanvas = new Canvas(mBitmap);
        Rect r;
        int translatedHue = 255 - (int) (mCurrentHue * 255 / 360);
        // Display all the colors of the hue bar with lines
        float pWidth=(float)width/(float)256;
        mPaint.setStrokeWidth(0);
        mPaint.setStyle(Paint.Style.FILL);

        for (int x = 0; x < 256; x++) {
            mPaint.setColor(mHueBarColors[x]);
            r=new Rect((int)(x*pWidth),0,(int)((x+1)*pWidth),height);
            mCanvas.drawRect(r,mPaint);
        }

    }

    public int getColor(int x) {
        int x_pos=Math.max(0, Math.min((int) (256 * x / 100), mHueBarColors.length - 1));
        return mHueBarColors[x_pos];
    }
}
