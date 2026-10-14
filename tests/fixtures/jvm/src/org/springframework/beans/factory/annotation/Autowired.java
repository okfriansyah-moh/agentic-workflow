package org.springframework.beans.factory.annotation;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
// Fixture annotation shape only; this does not run the Spring container.
@Retention(RetentionPolicy.RUNTIME)
public @interface Autowired { }
