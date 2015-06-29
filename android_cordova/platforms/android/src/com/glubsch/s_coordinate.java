package com.glubsch;

import android.location.Location;

/**
 * Created by windkol on 18.05.2015.
 */
class s_coordinate {
    private Location last_valid_location;
    private boolean valid=false;

    public s_coordinate()                     { super();    }
    public void setCoordinaes(Location loc) { this.last_valid_location=loc; valid=true;  }
    public Location getCoordinaes()         { return this.last_valid_location;   }
    public boolean isValid()                { return this.valid;   }
}
