package fixture
class Bad {
    fun branch(value: Int): Int {
        if (value > 0) {
            if (value > 1) {
                if (value > 2) {
                    if (value > 3) {
                        return value
                    }
                }
            }
        }
        return 0
    }
}
