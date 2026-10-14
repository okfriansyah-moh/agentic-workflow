package fixture.bad;
import org.springframework.beans.factory.annotation.Autowired;
public class FieldInjection {
    @Autowired private fixture.good.Store store;
}
