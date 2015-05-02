package com.example.kolja.alert_app;

/**
 * Created by kolja on 5/1/15.
 */
public class ListContainer {
    public String name;
    public int current_value;
    public boolean auto_modus;
    public int pin;

    public ListContainer(){
        super();
    }

    public ListContainer(String name, int current_value, boolean auto_modus, int pin){
        this.name=name;
        this.current_value=current_value;
        this.auto_modus=auto_modus;
        this.pin=pin;
    }
}
