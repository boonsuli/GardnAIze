package com.gardnaize.backend.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.gardnaize.backend.api.CreateGardenProjectRequest;
import com.gardnaize.backend.domain.Exposure;
import com.gardnaize.backend.domain.GardenProject;
import com.gardnaize.backend.domain.SoilType;
import com.gardnaize.backend.repository.GardenProjectRepository;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.web.server.ResponseStatusException;

@ExtendWith(MockitoExtension.class)
class GardenProjectServiceTest {
    @Mock
    private GardenProjectRepository repository;

    private GardenProjectService service;

    @BeforeEach
    void setUp() {
        service = new GardenProjectService(repository);
    }

    @Test
    void createsGarden() {
        when(repository.save(any(GardenProject.class)))
                .thenAnswer(invocation -> invocation.getArgument(0));

        var created = service.create(new CreateGardenProjectRequest(
                "My garden", "Paris", Exposure.FULL_SUN, SoilType.LOAMY
        ));

        assertThat(created.name()).isEqualTo("My garden");
        assertThat(created.id()).isNotNull();
        verify(repository).save(any(GardenProject.class));
    }

    @Test
    void missingGardenReturnsNotFound() {
        UUID id = UUID.randomUUID();
        when(repository.findById(id)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.get(id))
                .isInstanceOf(ResponseStatusException.class)
                .hasMessageContaining("404");
    }
}
