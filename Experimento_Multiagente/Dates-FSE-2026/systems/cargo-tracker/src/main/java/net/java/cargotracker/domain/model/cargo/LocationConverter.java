package net.java.cargotracker.domain.model.cargo;

import javax.enterprise.context.RequestScoped;
import javax.faces.component.UIComponent;
import javax.faces.context.FacesContext;
import javax.faces.convert.Converter;
import javax.inject.Inject;
import javax.inject.Named;
import net.java.cargotracker.interfaces.booking.facade.dto.Location;

/**
 * JSF Converter for Location.
 *
 * @author Stephan Knitelius <stephan@knitelius.com>
 */
@Named
@RequestScoped
public class LocationConverter implements Converter {

    @Inject
    private BookingBackingBean backing;

    @Override
    public Object getAsObject(FacesContext context, UIComponent component, String value) {
        if (value != null) {
            for (Location location : backing.getLocations()) {
                if (location.getUnLocode().equals(value)) {
                    return location;
                }
            }
        }
        return null;
    }

    @Override
    public String getAsString(FacesContext context, UIComponent component, Object value) {
        return value == null ? "" : ((Location) value).getUnLocode();
    }

}
