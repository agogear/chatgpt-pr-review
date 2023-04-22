package com.uomrecruit.controllers;

import com.uomrecruit.dtos.SchoolGetDto;
import com.uomrecruit.dtos.SchoolPutDto;
import com.uomrecruit.dtos.SchoolPostDto;import com.uomrecruit.services.SchoolService;
import io.swagger.annotations.ApiOperation;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.logging.log4j.Logger;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import com.uomrecruit.exceptions.UserNotFoundException;
import org.slf4j.LoggerFactory;

import javax.validation.constraints.NotNull;

@Slf4j
@RestController
@RequiredArgsConstructor
@Validated
@RequestMapping("/schools")
public class SchoolController {
    private final SchoolService schoolService;

    @GetMapping("/{id}")
    @ApiOperation(value="get school's info according to the school email")
    public ResponseEntity findSchoolDetailsById(@PathVariable("id") @NotNull Long id){
        SchoolGetDto schoolGetDto = schoolService.findById(id);
        return ResponseEntity.ok(schoolGetDto);
    }

    @PostMapping("/signup")
    public ResponseEntity createUser(@RequestBody SchoolPostDto schoolPostDto) {
        if (schoolService.ifEmailExists(schoolPostDto.getEmail())) {
            log.info("email: {} already exists", schoolPostDto.getEmail());
            return new ResponseEntity<>("Email has taken", HttpStatus.CONFLICT);
        }
        log.info("email: {}, name: {}", schoolPostDto.getEmail(), schoolPostDto.getSchoolName());
        schoolService.createSchoolAccount(schoolPostDto);

        return ResponseEntity.ok("success");
    }

    @PutMapping("/{id}")
    public ResponseEntity<String> updateSchool(@PathVariable("id") @NotNull Long id, @RequestBody SchoolPutDto schoolPutDto) {
        try {
            schoolService.updateSchoolAccount(id, schoolPutDto);
            return ResponseEntity.ok("School updated successfully.");
        } catch (UserNotFoundException e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(e.getMessage());
        }
    }




}
