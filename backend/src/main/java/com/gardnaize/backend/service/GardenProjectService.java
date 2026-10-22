package com.gardnaize.backend.service;

import com.gardnaize.backend.api.CreateGardenProjectRequest;
import com.gardnaize.backend.api.GardenProjectResponse;
import com.gardnaize.backend.domain.GardenProject;
import com.gardnaize.backend.repository.GardenProjectRepository;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
public class GardenProjectService {
    private final GardenProjectRepository repository;

    public GardenProjectService(GardenProjectRepository repository) {
        this.repository = repository;
    }

    @Transactional
    public GardenProjectResponse create(CreateGardenProjectRequest request) {
        GardenProject project = new GardenProject(
                request.name(), request.location(), request.exposure(), request.soilType()
        );
        return GardenProjectResponse.from(repository.save(project));
    }

    @Transactional(readOnly = true)
    public List<GardenProjectResponse> list() {
        return repository.findAll(Sort.by(Sort.Direction.DESC, "createdAt"))
                .stream()
                .map(GardenProjectResponse::from)
                .toList();
    }

    @Transactional(readOnly = true)
    public GardenProjectResponse get(UUID id) {
        return repository.findById(id)
                .map(GardenProjectResponse::from)
                .orElseThrow(() -> new ResponseStatusException(
                        HttpStatus.NOT_FOUND, "Garden project not found"
                ));
    }
}
