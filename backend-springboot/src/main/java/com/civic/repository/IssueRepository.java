package com.civic.repository;

import com.civic.model.Issue;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface IssueRepository extends JpaRepository<Issue, Long> {
    List<Issue> findByCategoryIdOrderByVoteCountDescCreatedAtDesc(Long categoryId);
    
    @Query("SELECT i FROM Issue i WHERE i.locationLat BETWEEN ?1 AND ?2 AND i.locationLong BETWEEN ?3 AND ?4")
    List<Issue> findByLocationRange(double minLat, double maxLat, double minLng, double maxLng);
    
    List<Issue> findAllByOrderByVoteCountDescCreatedAtDesc();
}