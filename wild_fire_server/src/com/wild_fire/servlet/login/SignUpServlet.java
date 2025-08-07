package com.wild_fire.servlet.login;

import javax.servlet.http.*;
import javax.servlet.annotation.*;
import java.io.IOException;
import java.io.InputStream;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.util.Properties;
import org.mindrot.jbcrypt.BCrypt;

import static java.lang.System.out;

@WebServlet("/signup")
public class SignUpServlet extends HttpServlet {
    protected void doPost(HttpServletRequest request, HttpServletResponse response) throws IOException {
        request.setCharacterEncoding("UTF-8");

        String userId = request.getParameter("user_id");
        String userRawPw = request.getParameter("user_pw");
        String userName = request.getParameter("user_name");

        // 입력값 검증
        if (userId == null || userId.trim().isEmpty() || 
            userRawPw == null || userRawPw.isEmpty() || 
            userName == null || userName.trim().isEmpty()) {
            
            response.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            response.getWriter().write("{\"result\": \"fail\", \"message\": \"모든 필드를 입력해주세요.\"}");
            return;
        }

        String userHashedPw = BCrypt.hashpw(userRawPw, BCrypt.gensalt());
        String sql = "INSERT INTO users (u_id, user_id, user_pw, user_name) VALUES (users_seq.NEXTVAL, ?, ?, ?)";

        // try-with-resources를 사용하여 DB 연결 및 자원 자동 해제
        try (Connection conn = com.wild_fire.util.DBUtil.getConnection();
             PreparedStatement pstmt = conn.prepareStatement(sql)) {

            // AutoCommit 비활성화 (명시적 트랜잭션 관리)
            conn.setAutoCommit(false);

            pstmt.setString(1, userId);
            pstmt.setString(2, userHashedPw);
            pstmt.setString(3, userName);

            int result = pstmt.executeUpdate();
            response.setContentType("application/json; charset=UTF-8");

            if (result > 0) {
                conn.commit(); // ★★★ 변경 사항을 데이터베이스에 최종 확정
                System.out.println("회원가입 성공 및 커밋 완료: " + userId);
                response.getWriter().write("{\"result\": \"success\"}");
            } else {
                conn.rollback(); // 실패 시 롤백
                response.getWriter().write("{\"result\": \"fail\", \"message\": \"회원가입에 실패했습니다.\"}");
            }

        } catch (java.sql.SQLIntegrityConstraintViolationException e) {
            // 아이디나 이메일 중복 시 발생하는 예외
            e.printStackTrace();
            response.setStatus(HttpServletResponse.SC_CONFLICT); // 409 Conflict
            response.getWriter().write("{\"result\": \"fail\", \"message\": \"이미 존재하는 아이디입니다.\"}");
        
        } catch (Exception e) {
            e.printStackTrace();
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            response.getWriter().write("{\"result\": \"error\", \"message\": \"서버 오류가 발생했습니다.\"}");
        }
    }
}