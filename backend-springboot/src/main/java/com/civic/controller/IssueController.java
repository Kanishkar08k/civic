package com.civic.controller;

import com.civic.model.Issue;
import com.civic.repository.IssueRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/issues")
@CrossOrigin(origins = "*")
public class IssueController {

    @Autowired
    private IssueRepository issueRepository;

    @PostMapping
    public ResponseEntity<Map<String, Object>> createIssue(@RequestBody Issue issue) {
        Map<String, Object> response = new HashMap<>();
        
        try {
            if (issue.getVoiceBase64() != null && !issue.getVoiceBase64().isEmpty()) {
                issue.setVoiceTranscript("Voice note recorded (transcription available in full version)");
            }
            
            Issue savedIssue = issueRepository.save(issue);
            
            response.put("success", true);
            response.put("issue", savedIssue);
            response.put("message", "Issue reported successfully");
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            response.put("success", false);
            response.put("message", "Failed to create issue: " + e.getMessage());
            return ResponseEntity.badRequest().body(response);
        }
    }

    @GetMapping
    public ResponseEntity<List<Issue>> getIssues(
            @RequestParam(required = false) Double lat,
            @RequestParam(required = false) Double lng,
            @RequestParam(defaultValue = "5.0") Double radius,
            @RequestParam(required = false) String categoryId) {
        
        try {
            List<Issue> issues;
            
            if (lat != null && lng != null) {
                double offset = 0.05; // Simple distance calculation
                issues = issueRepository.findByLocationRange(
                    lat - offset, lat + offset, lng - offset, lng + offset);
            } else if (categoryId != null && !categoryId.isEmpty()) {
                issues = issueRepository.findByCategoryIdOrderByVoteCountDescCreatedAtDesc(Long.parseLong(categoryId));
            } else {
                issues = issueRepository.findAllByOrderByVoteCountDescCreatedAtDesc();
            }
            
            return ResponseEntity.ok(issues);
            
        } catch (Exception e) {
            return ResponseEntity.badRequest().build();
        }
    }

    @GetMapping("/{issueId}")
    public ResponseEntity<Issue> getIssue(@PathVariable Long issueId) {
        Optional<Issue> issue = issueRepository.findById(issueId);
        return issue.map(ResponseEntity::ok).orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/{issueId}/vote")
    public ResponseEntity<Map<String, Object>> voteIssue(
            @PathVariable Long issueId, 
            @RequestBody Map<String, String> voteData) {
        
        Map<String, Object> response = new HashMap<>();
        
        try {
            Optional<Issue> optionalIssue = issueRepository.findById(issueId);
            if (optionalIssue.isPresent()) {
                Issue issue = optionalIssue.get();
                issue.setVoteCount(issue.getVoteCount() + 1);
                issueRepository.save(issue);
                
                response.put("success", true);
                response.put("voted", true);
                response.put("message", "Vote added");
                return ResponseEntity.ok(response);
            } else {
                response.put("success", false);
                response.put("message", "Issue not found");
                return ResponseEntity.notFound().build();
            }
            
        } catch (Exception e) {
            response.put("success", false);
            response.put("message", "Vote failed: " + e.getMessage());
            return ResponseEntity.badRequest().body(response);
        }
    }
}