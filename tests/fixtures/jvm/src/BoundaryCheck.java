import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.domain.JavaClasses;
import static com.tngtech.archunit.library.dependencies.SlicesRuleDefinition.slices;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noFields;
import org.springframework.beans.factory.annotation.Autowired;

public class BoundaryCheck {
    public static void main(String[] args) {
        JavaClasses classes = new ClassFileImporter().importPackages(args[0]);
        if (classes.isEmpty()) throw new IllegalStateException("Empty architecture selection");
        if (args[1].equals("cycles")) {
            slices().matching("fixture.bad.(*)..").should().beFreeOfCycles().check(classes);
        } else {
            noFields().should().beAnnotatedWith(Autowired.class).check(classes);
        }
    }
}
