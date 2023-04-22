package com.uomrecruit.services;

import com.uomrecruit.dtos.SchoolGetDto;
import com.uomrecruit.dtos.SchoolPutDto;
import com.uomrecruit.dtos.SchoolPostDto;import com.uomrecruit.models.School;import com.uomrecruit.repositories.SchoolRepository;
import com.uomrecruit.utility.mapper.SchoolMapper;
import java.util.Optional;
import javax.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import com.uomrecruit.exceptions.UserNotFoundException;

@Slf4j
@Service
@RequiredArgsConstructor

public class SchoolService {
    private final SchoolMapper schoolMapper;
    private final SchoolRepository schoolRepository;


    public SchoolGetDto findById(Long id) {
        return schoolRepository.findById(id).map(schoolMapper::mapSchoolEntityToDto).orElseThrow(RuntimeException::new);
    }

    public boolean ifEmailExists(String email) {
        return schoolRepository.findByEmail(email).isPresent();
    }


    public void createSchoolAccount(SchoolPostDto schoolPostDto) {
        School school = schoolMapper.mapSchoolDtoToEntity(schoolPostDto);
        schoolRepository.save(school);
    }


    @Transactional
    public void updateSchoolAccount(Long id, SchoolPutDto schoolPutDto) {
        int updatedRowCount = schoolRepository.updateSchoolById(
            id,
            schoolPutDto.getSchoolName(),
            schoolPutDto.getContactName(),
            schoolPutDto.getContactEmail(),
            schoolPutDto.getWebAddress(),
            schoolPutDto.getSector(),
            schoolPutDto.getYearLevels(),
            schoolPutDto.getImage()
        );

        if (updatedRowCount != 1) {
            // Handle the case where the school with the given ID doesn't exist
            throw new UserNotFoundException("School not found for ID: " + id);
        }
    }
}


