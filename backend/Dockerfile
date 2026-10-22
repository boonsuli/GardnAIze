# syntax=docker/dockerfile:1
FROM maven:3.9.11-eclipse-temurin-25 AS build
WORKDIR /workspace
COPY pom.xml ./
RUN mvn -B -q dependency:go-offline
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
