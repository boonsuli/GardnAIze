package com.gardnaize.backend.config;

import java.util.concurrent.Executor;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

/** Separate bounded I/O executors prevent slow providers from starving other modules. */
@Configuration
public class AsyncModuleConfiguration {
    private Executor pool(String prefix, int core, int max, int queue) {
        var executor = new ThreadPoolTaskExecutor();
        executor.setThreadNamePrefix(prefix);
        executor.setCorePoolSize(core);
        executor.setMaxPoolSize(max);
        executor.setQueueCapacity(queue);
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(15);
        executor.setRejectedExecutionHandler(new java.util.concurrent.ThreadPoolExecutor.AbortPolicy());
        executor.initialize();
        return executor;
    }

    @Bean("validationExecutor")
    public Executor validationExecutor() {
        return pool("gdai-valid-", 2, 4, 32);
    }

    @Bean("visionExecutor")
    public Executor visionExecutor() {
        return pool("gdai-vision-", 2, 4, 16);
    }

    @Bean("plantExecutor")
    public Executor plantExecutor() {
        return pool("gdai-plant-", 2, 4, 32);
    }
}
