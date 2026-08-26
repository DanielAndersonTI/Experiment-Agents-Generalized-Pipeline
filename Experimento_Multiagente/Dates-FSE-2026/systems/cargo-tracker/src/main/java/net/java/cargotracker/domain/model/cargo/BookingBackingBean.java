package net.java.cargotracker.domain.model.cargo;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import javax.annotation.PostConstruct;
import javax.faces.application.FacesMessage;
import javax.faces.context.FacesContext;
import javax.faces.flow.FlowScoped;
import javax.inject.Inject;
import javax.inject.Named;
import static net.java.cargotracker.application.util.DateUtil.computeDuration;
import net.java.cargotracker.interfaces.booking.facade.BookingServiceFacade;
import net.java.cargotracker.interfaces.booking.facade.dto.Location;
import org.primefaces.context.RequestContext;

/**
 *
 * @author davidd
 */
@Named
@FlowScoped("booking")
public class BookingBackingBean implements Serializable {

    private static final long serialVersionUID = 1L;
    private static final String FORMAT = "yyyy-MM-dd";
    List<Location> locations;
    private Date arrivalDeadline;

    private Location origin;
    private Location destination;

    private String newTrackingId = null;
    private Date today = new Date();
    private boolean bookable = false;
    private long duration = -1;
    private final long MIN_JOURNEY_DURATION = 1; // journey should be 1 day min.

    @Inject
    private BookingServiceFacade bookingServiceFacade;

    @PostConstruct
    public void init() {
        locations = bookingServiceFacade.listShippingLocations();
    }

    public List<Location> getLocations() {
        return locations;
    }

    public List<Location> getDestinations() {
        List<Location> availableDestinations = new ArrayList<>(locations);
        availableDestinations.remove(origin);
        return availableDestinations;
    }

    public List<Location> getOrigins() {
        List<Location> availableOrigins = new ArrayList<>(locations);
        availableOrigins.remove(destination);
        return availableOrigins;
    }

    public Location getOrigin() {
        return origin;
    }

    public void setOrigin(Location origin) {
        this.origin = origin;
    }

    public Location getDestination() {
        return destination;
    }

    public void setDestination(Location destination) {
        this.destination = destination;
    }

    public Date getArrivalDeadline() {
        return arrivalDeadline;
    }

    public Date getToday() {
        return today;
    }

    public long getDuration() {
        return duration;
    }

    public void setArrivalDeadline(Date arrivalDeadline) {
        this.arrivalDeadline = arrivalDeadline;
    }

    public String getNewTrackingId() {
        return newTrackingId;
    }

    public boolean isBookable() {
        return bookable;
    }

    public String register() {

        String trackingId = null;
        try {
            if (!origin.equals(destination)) {
                trackingId = bookingServiceFacade.bookNewCargo(
                        origin.getUnLocode(),
                        destination.getUnLocode(),
                        //new SimpleDateFormat(FORMAT).parse(arrivalDeadline));
                        //new SimpleDateFormat("EEE MMM dd HH:mm:ss zzz yyyy").parse(arrivalDeadline)); // davidd
                        arrivalDeadline);

            } else {
                FacesContext context = FacesContext.getCurrentInstance();
                // UI now prevents from selecting same origin/destination
                FacesMessage message = new FacesMessage("Origin and destination cannot be the same.");
                message.setSeverity(FacesMessage.SEVERITY_ERROR);
                context.addMessage(null, message);
                return null;
            }
        } catch (Exception e) {
            throw new RuntimeException("Error parsing date", e); // todo, not parsing anymore
        }
        //return "show_original.xhtml?faces-redirect=true&trackingId=" + trackingId;
        return "/admin/dashboard.xhtml";
    }

    public String getReturnValue() {
        return "/admin/track";
    }

    public void deadlineUpdated() {
        duration = computeDuration(arrivalDeadline);
        if (duration >= MIN_JOURNEY_DURATION) {
            bookable = true;
        } else {
            bookable = false;
        }
        RequestContext.getCurrentInstance().update("dateForm:durationPanel");
        RequestContext.getCurrentInstance().update("dateForm:bookBtn");
    }

}
