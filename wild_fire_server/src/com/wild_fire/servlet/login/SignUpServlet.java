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

        Connection conn = null;
        PreparedStatement pstmt = null;

        try {
            // DB 연결 (본인 환경 맞게 수정)
            Properties props = new Properties();
            try (InputStream in = getClass().getClassLoader().getResourceAsStream("main/resources/db.properties")) {
                props.load(in);
            }

            String driver = props.getProperty("db.driver");
            String url = props.getProperty("db.url");
            String user = props.getProperty("db.user");
            String password = props.getProperty("db.password");

            Class.forName(driver);
            conn = DriverManager.getConnection(url, user, password);

            // 회원 정보 insert
            out.print(userId);
            out.print(userRawPw);
            out.print(userName);
            String userPw = BCrypt.hashpw(userRawPw, BCrypt.gensalt());
            String sql = "INSERT INTO users (u_id, user_id, user_pw, user_name) VALUES (users_seq.NEXTVAL, ?, ?, ?)";
            pstmt = conn.prepareStatement(sql);
            pstmt.setString(1, userId);
            pstmt.setString(2, userPw);
            pstmt.setString(3, userName);

            int result = pstmt.executeUpdate();
            response.setContentType("application/json");
            if (result > 0) {
                response.getWriter().write("{\"result\": \"success\"}");
            } else {
                response.getWriter().write("{\"result\": \"fail\"}");
            }
        } catch (Exception e) {
            e.printStackTrace();
            response.getWriter().write("{\"result\": \"error\"}");
        } finally {
            try { if (pstmt != null) pstmt.close(); } catch (Exception e) {}
            try { if (conn != null) conn.close(); } catch (Exception e) {}
        }
    }
}