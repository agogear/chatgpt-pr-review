package com.uomrecruit.controllers;

import javax.validation.constraints.NotNull;

import com.uomrecruit.dtos.StudentGetDto;
import com.uomrecruit.dtos.StudentPostDto;
import com.uomrecruit.services.StudentService;
import io.swagger.annotations.ApiOperation;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequiredArgsConstructor
@Validated
@RequestMapping("/students")
public class StudentController {
    private final StudentService studentService;

    @GetMapping("/{id}")
    @ApiOperation(value = "get student's info according to the student id")
    public ResponseEntity getName(@PathVariable("id") @NotNull Long id) {
        StudentGetDto studentGetDto = studentService.findById(id);
        return ResponseEntity.ok(studentGetDto);
    }

    @PostMapping("/login")
    @ApiOperation(value="student login")
    public ResponseEntity login() {
        return ResponseEntity.ok("success");
    }

    @PostMapping("/signup")
    public ResponseEntity createStudent(@RequestBody StudentPostDto studentPostDto)
    {
        if(studentService.ifEmailExists(studentPostDto.getEmail()))
        {
            log.info("email: {} already exists", studentPostDto.getEmail());
            return new ResponseEntity<>("Email has taken", HttpStatus.CONFLICT);
        }
        if(studentService.checkEmail(studentPostDto.getEmail())==false){
            log.info("You must enter a unimelb student email");
            return new ResponseEntity<>("Invalid Email",HttpStatus.CONFLICT);

        }
        log.info("email: {}, number: {}", studentPostDto.getEmail(), studentPostDto.getStudentNumber());
        studentService.createStudentAccount(studentPostDto);
        return ResponseEntity.ok("success");
    }
}
