package com.illumino.android_webapp;

import android.location.Location;

import java.util.ArrayList;

/**
 * Created by windkol on 18.05.2015.
 */
class s_area {
    private String name;
    private Integer detection;
    private Location coordinates;
    private Integer range;
    private Integer state; // debugging
    public ArrayList<String> clients = new ArrayList<String>();

    public s_area(String name, Integer detection, Location coordinates, Integer range, Integer state, String client){
        super();
        this.name=name;                 // like "home"
        this.detection=detection;       // 0=off, 1=on, 2=fast fire
        this.coordinates=coordinates;   // a android location
        this.range = range;         // range around the center
        this.state=state;
        this.clients.clear();
        this.clients.add(client);
    }

    public void setState(int st) {          this.state=st;              }
    public void setDetection(int det){      this.detection=det;         }
    public int getCriticalRange(){          return this.range;       }
    public int getDetection()   {           return this.detection;      }
    public String getName()     {           return this.name;           }
    public int getState()       {           return this.state;       }
    public Location getCoordinates() {      return this.coordinates;    }
}
