package com.civic.controller;

import com.civic.model.Category;
import com.civic.repository.CategoryRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/categories")
@CrossOrigin(origins = "*")
public class CategoryController {

    @Autowired
    private CategoryRepository categoryRepository;

    @GetMapping
    public ResponseEntity<List<Category>> getCategories() {
        List<Category> categories = categoryRepository.findAll();
        return ResponseEntity.ok(categories);
    }

    @PostMapping("/init")
    public ResponseEntity<Map<String, Object>> initCategories() {
        Map<String, Object> response = new HashMap<>();
        
        try {
            // Clear existing categories
            categoryRepository.deleteAll();
            
            // Create default categories
            List<Category> defaultCategories = Arrays.asList(
                new Category("Roads & Transportation", "Potholes, traffic issues, road repairs", "car"),
                new Category("Water & Sanitation", "Water leaks, drainage, sewage", "water-drop"),
                new Category("Electricity", "Power outages, street lights, electrical issues", "flash"),
                new Category("Waste Management", "Garbage collection, littering, recycling", "trash"),
                new Category("Public Safety", "Security, crime, emergency services", "shield"),
                new Category("Parks & Recreation", "Parks maintenance, recreational facilities", "leaf"),
                new Category("Other", "Other civic issues", "help-circle")
            );
            
            categoryRepository.saveAll(defaultCategories);
            
            response.put("success", true);
            response.put("message", "Categories initialized");
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            response.put("success", false);
            response.put("message", "Failed to initialize categories: " + e.getMessage());
            return ResponseEntity.badRequest().body(response);
        }
    }
}