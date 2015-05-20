package com.example.kolja.Illumino;

/**
 * Created by kolja on 5/19/15.
 */
import java.util.ArrayList;
import java.util.List;

public class areas {

    public String name;
    public final List<m2m_container> m2mList = new ArrayList<m2m_container>();

    public areas(String AreaName) {
        this.name = AreaName;
    }

}