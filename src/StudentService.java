package com.uomrecruit.services;

import com.uomrecruit.dtos.StudentGetDto;
import com.uomrecruit.dtos.StudentPostDto;
import com.uomrecruit.models.Student;
import com.uomrecruit.utility.mapper.StudentMapper;
import com.uomrecruit.repositories.StudentRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class StudentService {
    private final StudentRepository studentRepository;
    private final StudentMapper studentMapper;

    public StudentGetDto findById(Long id) {
        return studentRepository.findById(id).map(studentMapper::mapStudentEntityToDto).orElseThrow(RuntimeException::new);
    }
    public void createStudentAccount(StudentPostDto studentPostDto) {
        Student student = studentMapper.mapStudentDtoToEntity(studentPostDto);
        studentRepository.save(student);
    }

    public boolean ifEmailExists(String email) {
        return studentRepository.findByEmail(email).isPresent();
    }

    public boolean checkEmail(String email){
        if(email.contains("@student.unimelb.edu.au")){
            return true;
        }
        return false;
    }
}
