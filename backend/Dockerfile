# syntax=docker/dockerfile:1
FROM maven:3.9.11-eclipse-temurin-25 AS build
WORKDIR /workspace
COPY pom.xml ./
# Maven Central may briefly return missing metadata during a cold Docker build.
# Retry dependency resolution only; persistent POM errors still fail the build.
RUN set -eu; \
    for attempt in 1 2 3; do \
        if mvn -B -U -q dependency:go-offline; then \
            break; \
        fi; \
        if [ "$attempt" -eq 3 ]; then \
            exit 1; \
        fi; \
        echo "Maven dependency resolution failed (attempt $attempt/3); retrying..."; \
        sleep 10; \
    done
COPY src ./src
RUN mvn -B -q -DskipTests package

FROM amazoncorretto:25-alpine
WORKDIR /app
RUN addgroup -S app && adduser -S -G app app
COPY --from=build /workspace/target/gardnaize-backend-0.1.0-SNAPSHOT.jar /app/app.jar
USER app
EXPOSE 8081
ENV JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=65.0"
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
