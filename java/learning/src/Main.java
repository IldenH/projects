import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Scanner;
import java.math.BigInteger;
import java.math.BigDecimal;

/**
 * A Main class with a main function
 * @version 1.0
 * @author Me
 */
public class Main {
  public static void main(String[] args) throws IOException {
    System.out.println("Hello world!"); // comment
    int oneMillion = 1_000_000;
    System.out.println(oneMillion);
    byte small = 72;
    System.out.println(small - 30);
    System.out.println(Math.PI - 3.2f);
    System.out.println(1.7e308);
    System.out.println("日本語上手");
    double money;
    long people;
    int days;
    boolean isRed;
    String exampleText;
    int へい = 3;
    System.out.println(へい);
    var myVar = true;
    var myInt = 67;
    final double SEK_TO_NOK = 1.06;
    System.out.println(NOK_TO_SEK);

    enum Size { SMALL, MEDIUM, LARGE, EXTRA_LARGE };
    Size s = Size.MEDIUM;

    System.out.println(Math.floorMod(12 + 3, 12));
    var safeMultiply = Math.multiplyExact(3, 3); // exception instead of wrapping around

    System.out.println(3 > 1 ? "hei" : "nei");
    int n = 7;
    int m = 7;
    int fourteen = 2 * n++;
    int sixteen = 2 * ++m;

    int seasonCode = 4;
    String season = switch (seasonCode) {
      case 0 -> "Spring";
      case 1 -> "Summer";
      case 2 -> "Fall";
      case 3 -> "Winter";
      default -> null;
    };
    System.out.println(season);

    String hello = "Hello 私";
    System.out.println(hello.substring(0, 3));
    System.out.println(hello.substring(6, 7));

    "Hello".equals("Hello");
    "Hello".equalsIgnoreCase("hello");
    // not this: (merely checks if same location on heap):
    // "Hello" == "Hello";

    System.out.println("Hello".charAt(3));

    String emojiStr = "😭🤬";
    int[] codePoints = emojiStr.codePoints().toArray();
    for (int i = 0; i < codePoints.length; i++) {
      int cp = emojiStr.codePointAt(i);
      String str = Character.toString(cp);
      System.out.println(str);
    }
    String emojiStrNew = new String(codePoints, 0, codePoints.length);
    System.out.println(emojiStrNew);

    StringBuilder strBuilder = new StringBuilder();
    strBuilder.append("hei");
    strBuilder.append(", verden!");
    strBuilder.setCharAt(2, 'I');
    strBuilder.insert(4, " deg og ");
    System.out.println(strBuilder.toString());

    String html =
    // html
    """
<div class="something">
  Given the circumstances, I would proudly determine you.
</div>
    """;
    System.out.println(html);

    // Scanner in = new Scanner(System.in);
    // System.out.print("Name: ");
    // String name = in.nextLine();
    // System.out.println("Hello " + name + "!");

    // Console cons = System.console();
    // String username = cons.readLine("Username: ");
    // char[] password = cons.readPassword("Password: ");

    System.out.printf("%8.2f\n", 1000.0 / 3.0);
    System.out.printf("%.2e\n", 1000.0 / 3.0);
    System.out.printf("%,+(#.2f\n", 1_000_000_000.0 / 3.0);

    try {
      Scanner in = new Scanner(Path.of("temperature.csv"), StandardCharsets.UTF_8);
      while (in.hasNext()) System.out.println(in.nextLine());
      in.close();
    } catch (IOException e) {
        throw new RuntimeException(e);
    }

    try {
      PrintWriter out = new PrintWriter("output.txt", StandardCharsets.UTF_8);
      out.println("Test");
      out.flush();
      out.close();
    } catch (IOException e) {
      throw new RuntimeException(e);
    }

    // runs once regardless of the condition in while when using do/while
    {
      int i = 5;
      do i++;
      while (i < 5);
      System.out.println(i);
    }

    BigInteger hundred = BigInteger.valueOf(100);
    BigInteger hugeInt = new BigInteger("84370984327598437598725432578340725843728075843927584732857480187385064351087956437154620721890985390674385643728650772940235764372657432675643982657067167836458437098432759843759872543257834072584372807584392758473285748018738506435108795643715462072189098539067438564372865077294023576437265743267564398265706716783645");
    System.out.println(hugeInt);
    BigDecimal smallPi = new BigDecimal(Double.toString(Math.PI));
    BigDecimal bigPi = new BigDecimal("3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628034825342117067982148086513282306647093844609550582231725359408128481117450284102701938521105559644622948954930381964428810975665933446128475648233786783165271201909145648566923460348610454326648213393607260249141273724587006606315588174881520920962829254091715364367892590360011330530548820466521384146951941511609433057270365759591953092186117381932611793105118548074462379962749567351885752724891227938183011949129833673362440656643086021394946395224737190702179860943702770539217176293176752384674818467669405132000568127145263560827785771342757789609173637178721468440901224953430146549585371050792279689258923542019956112129021960864034418159813629774771309960518707211349999998372978049951059731732816096318595024459455346908302642522308253344685035261931188171010003137838752886587533208381420617177669147303598253490428755468731159562863882353787593751957781857780532171226806613001927876611195909216420198938095257201065485863278865936153381827968230301952035301852968995773622599413891249721775283479131515574857242454150695950829533116861727855889075098381754637464939319255060400927701671139009848824012858361603563707660104710181942955596198946767");
    System.out.println(bigPi);
    System.out.println("Big π is " + compareText(bigPi.compareTo(smallPi)) + " small π.");

    int[] nums = new int[100];
    for (int i = 0; i < nums.length; i++)
      nums[i] = i;
    System.out.println(Arrays.toString(nums));

    for (int x : nums)
      System.out.print(x + "+");
    System.out.println();

    int[] newNums = Arrays.copyOf(nums, nums.length);

    String[][] board = new String[8][8];
    for (int i = 0; i < board.length; i++) {
      for (int j = 0; j < board[i].length; j++) {
        board[i][j] = j % 2 == (i % 2) ? "x" : "o";
      }
    }
    for (String[] row : board)
      System.out.println(Arrays.toString(row));
    System.out.println(Arrays.deepToString(board));
  }

  public static final double NOK_TO_SEK = 0.94;

  public static String compareText(int x) {
    if (x < 0) return "less than";
    else if (x == 0) return "equal to";
    else return "greater than";
  }

}
