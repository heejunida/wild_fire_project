package com.wild_fire.servlet.login;

import com.wild_fire.DAO.UserDAO;

import javax.servlet.http.*;
import javax.servlet.annotation.*;
import java.io.IOException;
import org.mindrot.jbcrypt.BCrypt;

@WebServlet("/resetPwWithoutOld")
public class ResetPwWithoutOldServlet extends HttpServlet {
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        System.out.println("[DEBUG] ResetPwWithoutOldServlet 진입!");
        try {
            req.setCharacterEncoding("UTF-8");
            String user_id = req.getParameter("user_id");
            String newPw = req.getParameter("new_pw");

            if (user_id == null || newPw == null) {
                resp.setContentType("application/json; charset=UTF-8");
                resp.getWriter().write("{\"result\":\"fail\", \"msg\":\"필수값 누락\"}");
                return;
            }

            // 새 비밀번호 해시 처리
            String hash = BCrypt.hashpw(newPw, BCrypt.gensalt());
            UserDAO dao = new UserDAO();
            boolean success = dao.updateUserPw(user_id, hash);

            resp.setContentType("application/json; charset=UTF-8");
            if (success) {
                resp.getWriter().write("{\"result\":\"success\"}");
            } else {
                resp.getWriter().write("{\"result\":\"fail\"}");
            }
        } catch (Exception e) {
            resp.setContentType("application/json; charset=UTF-8");
            resp.getWriter().write("{\"result\":\"fail\", \"msg\":\"" + e.getMessage() + "\"}");
            e.printStackTrace();
        }
    }
}