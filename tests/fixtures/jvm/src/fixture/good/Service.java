package fixture.good;
public class Service {
    private final Store store;
    public Service(Store store) { this.store = store; }
    public String lookup() { return store.lookup(); }
}
