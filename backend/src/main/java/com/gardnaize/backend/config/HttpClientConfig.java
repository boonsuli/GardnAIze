package com.gardnaize.backend.config;

import java.time.Duration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

@Configuration
public class HttpClientConfig {
    @Bean
    public RestClient aiRestClient(
            RestClient.Builder builder,
            @Value("${gardnaize.ai.base-url}") String baseUrl
    ) {
        return builder.baseUrl(baseUrl)
                .requestFactory(new org.springframework.http.client.SimpleClientHttpRequestFactory() {
                    {
                        setConnectTimeout(Duration.ofSeconds(3));
                        setReadTimeout(Duration.ofSeconds(15));
                    }
                })
                .build();
    }
}
