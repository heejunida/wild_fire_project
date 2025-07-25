package com.wild_fire.servlet.login;

import com.wild_fire.DAO.UserDAO;

import javax.servlet.http.*;
import javax.servlet.annotation.*;
import java.io.IOException;

@WebServlet("/resetPw")
public class ResetPwServlet extends HttpServlet {
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        System.out.println("[DEBUG] ResetPwServlet 진입!");
        try {
            req.setCharacterEncoding("UTF-8");
            String user_id = req.getParameter("user_id");
            String oldPw = req.getParameter("old_pw");
            String newPw = req.getParameter("new_pw");
            System.out.println("[DEBUG] 파라미터 user_id: " + user_id + ", old_pw: " + oldPw + ", new_pw: " + newPw);

            UserDAO dao = new UserDAO();

            // 1. DB에서 user_id로 기존 해시값 가져옴
            String dbHash = dao.getUserPwHash(user_id);
            System.out.println("[DEBUG] dbHash: " + dbHash);
            if (dbHash == null) {
                resp.setContentType("application/json; charset=UTF-8");
                resp.getWriter().write("{\"result\":\"fail\", \"msg\":\"비밀번호 정보가 없습니다.\"}");
                return;
            }
            boolean valid = org.mindrot.jbcrypt.BCrypt.checkpw(oldPw, dbHash);
            if (!valid) {
                resp.setContentType("application/json; charset=UTF-8");
                resp.getWriter().write("{\"result\":\"wrongpw\"}");
                return;
            }

            // 2. 새 비번 해시해서 업데이트
            String hash = org.mindrot.jbcrypt.BCrypt.hashpw(newPw, org.mindrot.jbcrypt.BCrypt.gensalt());
            boolean success = dao.updateUserPw(user_id, hash);

            resp.setContentType("application/json; charset=UTF-8");
            if (success) {
                resp.getWriter().write("{\"result\":\"success\"}");
                HttpSession session = req.getSession(false);
                session.invalidate();
            } else {
                resp.getWriter().write("{\"result\":\"fail\"}");
            }
        } catch (Exception e) {
            // 모든 예외를 잡아서 JSON 반환!
            resp.setContentType("application/json; charset=UTF-8");
            resp.getWriter().write("{\"result\":\"fail\", \"msg\":\"" + e.getMessage() + "\"}");
            e.printStackTrace(); // 콘솔에 예외 로그 남기기
        }
    }
}