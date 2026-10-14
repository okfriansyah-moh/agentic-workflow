package fixture
class Good(private val store: Store) {
    fun lookup(): String = store.lookup()
}
interface Store {
    fun lookup(): String
}
