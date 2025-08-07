package com.wild_fire.DAO;

import com.wild_fire.DTO.UserDTO;
import com.wild_fire.util.DBUtil;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

import org.mindrot.jbcrypt.BCrypt;

public class UserDAO {
    // 회원가입 (Insert)
    public int insertUser(String userId, String userPw, String userName) {
        String sql = "INSERT INTO users (user_id, user_pw, user_name) VALUES (?, ?, ?)";
        try (Connection conn = DBUtil.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, userId);
            ps.setString(2, userPw);
            ps.setString(3, userName);
            return ps.executeUpdate();
        } catch (SQLException e) {
            e.printStackTrace();
            return 0;
        }
    }

    // 로그인 (ID/PW 체크)
    public Long loginAndGetUid(String userId, String password) {
        String sql = "SELECT u_id, user_pw FROM users WHERE user_id = ?";
        
        System.out.println("\n--- [LOGIN ATTEMPT] ---");
        System.out.println("Trying to log in with user ID: " + userId);

        // try-with-resources 구문을 사용하여 자원을 자동으로 해제합니다.
        try (Connection conn = DBUtil.getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {
            
            pstmt.setString(1, userId);
            
            try (ResultSet rs = pstmt.executeQuery()) {
                if (rs.next()) {
                    String dbHashedPassword = rs.getString("user_pw");
                    System.out.println("User found. DB Hashed Password: " + dbHashedPassword);
                    System.out.println("Hashed Password Length: " + dbHashedPassword.length());

                    boolean passwordMatch = BCrypt.checkpw(password, dbHashedPassword);
                    System.out.println("Password match result (BCrypt.checkpw): " + passwordMatch);
                    
                    if (passwordMatch) {
                        System.out.println("Login SUCCESS. Returning u_id.");
                        System.out.println("-------------------------\n");
                        return rs.getLong("u_id");
                    }
                } else {
                    System.out.println("User NOT FOUND in database.");
                }
            }
        } catch (Exception e) {
            System.err.println("An unexpected error occurred during login process.");
            e.printStackTrace();
        }
        
        System.out.println("Login FAILED.");
        System.out.println("-------------------------\n");
        return null;
    }

    public UserDTO findUserById(String userId) {
        String sql = "SELECT user_id, user_name FROM users WHERE user_id = ?";
        try (Connection conn = DBUtil.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, userId);
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    UserDTO user = new UserDTO();
                    user.setUserId(rs.getString("user_id"));
                    user.setUserName(rs.getString("user_name"));
                    return user;
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    public String findUserIdByName(String userName) {
        String sql = "SELECT user_id, user_name FROM users WHERE user_name = ?";
        try (Connection conn = DBUtil.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, userName);
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) { // DB에 해당 이름을 가진 유저가 있으면
                    UserDTO user = new UserDTO();
                    String id = rs.getString("user_id");
                    return id; // 바로 리턴
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null; // 못 찾으면 null
    }

    public Boolean findUserPwByIdAndName(String userId, String userName) {
        String sql = "SELECT user_id, user_name FROM users WHERE user_id = ? AND user_name = ?";
        try (Connection conn = DBUtil.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, userId);
            ps.setString(2, userName);
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    UserDTO user = new UserDTO();
                    String id = rs.getString("user_id");
                    String name = rs.getString("user_name");
                    if (userId.equals(id)) {
                        if (userName.equals(name)) {
                            return true;
                        }
                    }
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return false;
    }

    // 비밀번호 변경 (비번은 반드시 bcrypt로 해시해서 넘겨야 함)
    public boolean updateUserPw(String userId, String hashPw) {
        String sql = "UPDATE users SET user_pw = ? WHERE user_id = ?";
        try (Connection conn = DBUtil.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, hashPw);
            ps.setString(2, userId);
            return ps.executeUpdate() == 1;
        } catch (Exception e) {
            e.printStackTrace();
        }
        return false;
    }

    public String getUserPwHash(String userId) {
        String sql = "SELECT user_pw FROM users WHERE user_id = ?";
        try (Connection conn = DBUtil.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, userId);
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) return rs.getString("user_pw");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }
    public Long getUidByUserId(String userId) throws Exception {
        String sql = "SELECT u_id FROM users WHERE user_id = ?";
        Long uid = null;

        try (Connection conn = DBUtil.getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {

            pstmt.setString(1, userId);
            try (ResultSet rs = pstmt.executeQuery()) {
                if (rs.next()) {
                    uid = rs.getLong("u_id");
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
            throw e;
        }

        return uid;
    }
}